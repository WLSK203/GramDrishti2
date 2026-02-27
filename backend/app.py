import os


from flask import Flask, jsonify, request
from flask_cors import CORS

from config import SECRET_KEY, CORS_ORIGINS
from database import get_connection, run_query, run_query_one

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
CORS(app, origins=CORS_ORIGINS, supports_credentials=True)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file found"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"success": False, "message": "Empty filename"}), 400

    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    return jsonify({
        "success": True,
        "message": "File uploaded successfully",
        "path": save_path
    })
def to_camel(d):
    """Convert dict keys from snake_case to camelCase for frontend. Leaves keys without underscore unchanged (e.g. redirectUrl)."""
    if d is None:
        return None
    if isinstance(d, list):
        return [to_camel(i) for i in d]
    if not isinstance(d, dict):
        return d
    out = {}
    for k, v in d.items():
        if "_" not in k:
            new_k = k
        else:
            parts = k.split("_")
            new_k = parts[0].lower() + "".join(p.capitalize() for p in parts[1:])
        out[new_k] = to_camel(v)
    return out


@app.route("/")
def index():
    return jsonify({"service": "GRAM-SABHA API", "status": "running"})


@app.route("/api/health")
def health():
    """Check API and database connectivity."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 AS ok")
                cur.fetchone()
        return jsonify({"status": "ok", "database": "connected"})
    except Exception as e:
        return jsonify({"status": "error", "database": str(e)}), 503


# ---------- Auth ----------
@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    """Login with mobile and pin. Returns user object for session."""
    data = request.get_json() or {}
    mobile = (data.get("mobile") or data.get("userId") or "").strip()
    password = (data.get("password") or data.get("pin") or "").strip()
    if not mobile or not password:
        return jsonify({"success": False, "error": "Mobile and password required"}), 400
    try:
        user = run_query_one(
            "SELECT id, external_id, name, name_hindi, role, role_name, mobile, village_id, ward, avatar, redirect_url, department, level FROM users WHERE mobile = %s AND pin = %s",
            (mobile, password),
        )
        if not user:
            return jsonify({"success": False, "error": "Invalid credentials"}), 401
        u = dict(user)
        u["redirectUrl"] = u.pop("redirect_url", None) or {"villager": "villager-dashboard.html", "sarpanch": "sarpanch-portal.html", "admin": "admin-panel.html"}.get(u["role"], "index.html")
        return jsonify({"success": True, "user": to_camel(u)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/auth/register", methods=["POST"])
def auth_register():
    """Create a new account (villager or sarpanch)."""
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    mobile = (data.get("mobile") or "").strip()
    pin = (data.get("pin") or data.get("password") or "").strip()
    role = (data.get("role") or "villager").strip().lower()
    village_id = data.get("villageId") or data.get("village_id")
    ward = (data.get("ward") or "").strip() or None

    if not name or not mobile or not pin:
        return jsonify({"success": False, "error": "Name, mobile and PIN are required"}), 400
    if len(mobile) < 10:
        return jsonify({"success": False, "error": "Mobile must be at least 10 digits"}), 400
    if len(pin) < 4:
        return jsonify({"success": False, "error": "PIN must be at least 4 characters"}), 400
    if role not in ("villager", "sarpanch"):
        return jsonify({"success": False, "error": "Role must be villager or sarpanch"}), 400

    try:
        existing = run_query_one("SELECT id FROM users WHERE mobile = %s", (mobile,))
        if existing:
            return jsonify({"success": False, "error": "This mobile number is already registered"}), 400

        role_name = "Villager" if role == "villager" else "Sarpanch"
        redirect_url = "villager-dashboard.html" if role == "villager" else "sarpanch-portal.html"
        avatar = "".join((w[0] if w else "") for w in name.split()[:2]).upper()[:2] or "U"
        import uuid
        external_id = f"{role[:3].upper()}-{uuid.uuid4().hex[:6].upper()}"

        if village_id is not None:
            village_id = int(village_id)
        else:
            village_id = None

        run_query(
            """INSERT INTO users (external_id, name, role, role_name, mobile, pin, village_id, ward, avatar, redirect_url)
             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (external_id, name, role, role_name, mobile, pin, village_id, ward, avatar, redirect_url),
            commit=True,
        )
        return jsonify({"success": True, "message": "Account created. You can now log in."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/auth/check-mobile")
def auth_check_mobile():
    """Return role info for a mobile (for login page role detection). No password."""
    mobile = (request.args.get("mobile") or "").strip()
    if not mobile or len(mobile) < 10:
        return jsonify({"found": False})
    try:
        row = run_query_one(
            "SELECT role, role_name FROM users WHERE mobile = %s",
            (mobile,),
        )
        if not row:
            return jsonify({"found": False})
        return jsonify({"found": True, "role": row["role"], "roleName": row["role_name"]})
    except Exception:
        return jsonify({"found": False})


# ---------- Villages ----------
@app.route("/api/villages")
def list_villages():
    try:
        rows = run_query(
            "SELECT id, name, name_hindi, district, state, pincode, population, households, sarpanch_name, panchayat_code FROM villages ORDER BY name LIMIT 100"
        )
        return jsonify({"success": True, "data": to_camel(rows)})
    except Exception:
        return jsonify({"success": True, "data": []})


@app.route("/api/villages/<int:village_id>")
def get_village(village_id):
    try:
        row = run_query_one(
            "SELECT id, name, name_hindi, district, state, pincode, population, households, sarpanch_name, panchayat_code FROM villages WHERE id = %s",
            (village_id,),
        )
        if not row:
            return jsonify({"success": False, "error": "Not found"}), 404
        return jsonify({"success": True, "data": to_camel(dict(row))})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------- Issues ----------
@app.route("/api/issues")
def list_issues():
    village_id = request.args.get("village_id", type=int)
    user_id = request.args.get("user_id", type=int)  # to compute userVoted
    try:
        if village_id:
            if user_id:
                rows = run_query(
                    """
                    SELECT i.id, i.external_id, i.title, i.title_hindi, i.description, i.category, i.category_name,
                           i.status, i.status_name, i.priority, i.department, i.reported_by_name, i.reported_date,
                           i.votes, i.location, i.progress, i.contractor, i.estimated_cost, i.created_at,
                           EXISTS (SELECT 1 FROM issue_votes v WHERE v.issue_id = i.id AND v.user_id = %s) AS user_voted
                    FROM issues i
                    WHERE i.village_id = %s
                    ORDER BY i.created_at DESC
                    LIMIT 50
                    """,
                    (user_id, village_id),
                )
            else:
                rows = run_query(
                    """
                    SELECT id, external_id, title, title_hindi, description, category, category_name,
                           status, status_name, priority, department, reported_by_name, reported_date,
                           votes, location, progress, contractor, estimated_cost, created_at,
                           false AS user_voted
                    FROM issues
                    WHERE village_id = %s
                    ORDER BY created_at DESC
                    LIMIT 50
                    """,
                    (village_id,),
                )
        else:
            rows = run_query(
                """
                SELECT id, external_id, title, title_hindi, description, category, category_name,
                       status, status_name, priority, department, reported_by_name, reported_date,
                       votes, location, progress, contractor, estimated_cost, created_at
                FROM issues
                ORDER BY created_at DESC
                LIMIT 50
                """
            )
            if user_id and rows:
                for r in rows:
                    r["user_voted"] = bool(
                        run_query_one("SELECT 1 FROM issue_votes WHERE issue_id = %s AND user_id = %s", (r["id"], user_id))
                    )
            else:
                for r in rows:
                    r["user_voted"] = False
        # Normalize for frontend (external_id as id if frontend expects string id)
        for r in rows:
            r["id"] = r.get("external_id") or str(r["id"])
        return jsonify({"success": True, "data": to_camel(rows)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "data": []}), 500


@app.route("/api/issues", methods=["POST"])
def create_issue():
    """Create a new issue/complaint (typically by a villager)."""
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    category = (data.get("category") or "").strip().lower()
    village_id = data.get("villageId") or data.get("village_id")
    reported_by_id = data.get("reportedById") or data.get("reported_by_id")
    location = (data.get("location") or "").strip() or None
    priority = (data.get("priority") or "normal").strip().lower()
    department = (data.get("department") or "").strip() or None

    if not title:
        return jsonify({"success": False, "error": "Title is required"}), 400
    if not village_id:
        return jsonify({"success": False, "error": "villageId is required"}), 400
    if not reported_by_id:
        return jsonify({"success": False, "error": "reportedById is required"}), 400

    try:
        village_id = int(village_id)
        reported_by_id = int(reported_by_id)
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "villageId and reportedById must be numeric"}), 400

    category_names = {
        "water": "Water Supply",
        "roads": "Roads & Paths",
        "electricity": "Electricity",
        "sanitation": "Hygiene & Sanitation",
        "education": "Education",
    }
    status = "submitted"
    status_name = "Submitted"

    from datetime import date
    import uuid

    external_id = f"ISS-{uuid.uuid4().hex[:8].upper()}"
    reported_date = date.today()

    try:
        reporter = run_query_one("SELECT name FROM users WHERE id = %s", (reported_by_id,))
        reported_by_name = reporter["name"] if reporter else None

        run_query(
            """
            INSERT INTO issues (
                external_id, title, description, category, category_name,
                status, status_name, priority, department, village_id,
                reported_by_id, reported_by_name, reported_date, votes, location
            ) VALUES (%s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s)
            """,
            (
                external_id,
                title,
                description or None,
                category or None,
                category_names.get(category, category.title() or None),
                status,
                status_name,
                priority,
                department,
                village_id,
                reported_by_id,
                reported_by_name,
                reported_date,
                0,
                location,
            ),
            commit=True,
        )

        new_issue = run_query_one(
            """
            SELECT id, external_id, title, description, category, category_name,
                   status, status_name, priority, department, village_id,
                   reported_by_id, reported_by_name, reported_date, votes, location, created_at
            FROM issues
            WHERE external_id = %s
            """,
            (external_id,),
        )
        return jsonify({"success": True, "data": to_camel(dict(new_issue))}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/issues/<issue_id>/vote", methods=["POST"])
def issue_vote(issue_id):
    """Toggle vote for issue. Body: { user_id }. issue_id can be numeric id or external_id."""
    data = request.get_json() or {}
    user_id = data.get("user_id") or request.args.get("user_id")
    if user_id is None:
        return jsonify({"success": False, "error": "user_id required"}), 400
    try:
        user_id = int(user_id)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM issues WHERE id::text = %s OR external_id = %s", (str(issue_id), str(issue_id)))
                row = cur.fetchone()
                if not row:
                    return jsonify({"success": False, "error": "Issue not found"}), 404
                real_id = row["id"]
                cur.execute("SELECT 1 FROM issue_votes WHERE issue_id = %s AND user_id = %s", (real_id, user_id))
                voted = cur.fetchone()
                if voted:
                    cur.execute("DELETE FROM issue_votes WHERE issue_id = %s AND user_id = %s", (real_id, user_id))
                    cur.execute("UPDATE issues SET votes = GREATEST(0, votes - 1) WHERE id = %s", (real_id,))
                    conn.commit()
                    return jsonify({"success": True, "voted": False, "message": "Vote removed"})
                else:
                    cur.execute("INSERT INTO issue_votes (issue_id, user_id) VALUES (%s, %s) ON CONFLICT (issue_id, user_id) DO NOTHING", (real_id, user_id))
                    cur.execute("UPDATE issues SET votes = votes + 1 WHERE id = %s", (real_id,))
                    conn.commit()
                    return jsonify({"success": True, "voted": True, "message": "Vote recorded"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------- Budget ----------
@app.route("/api/budget")
def get_budget():
    village_id = request.args.get("village_id", type=int)
    try:
        if village_id:
            row = run_query_one(
                "SELECT total_received, total_spent, pending_approval, available, fiscal_year, last_updated FROM budget_summary WHERE village_id = %s",
                (village_id,),
            )
        else:
            row = run_query_one(
                "SELECT village_id, total_received, total_spent, pending_approval, available, fiscal_year, last_updated FROM budget_summary ORDER BY id LIMIT 1"
            )
        if not row:
            return jsonify({"success": True, "data": {"totalReceived": 0, "totalSpent": 0, "pendingApproval": 0, "available": 0, "fiscalYear": "", "projects": []}})
        vid = village_id or row.get("village_id")
        projects = run_query(
            "SELECT external_id, name, sanctioned, released, spent, progress, status, contractor, start_date, deadline, completed_date, verifications_photos, verifications_gps, verifications_community, verifications_audit FROM projects WHERE village_id = %s ORDER BY id",
            (vid,),
        ) if vid else run_query(
            "SELECT external_id, name, sanctioned, released, spent, progress, status, contractor, start_date, deadline, completed_date, verifications_photos, verifications_gps, verifications_community, verifications_audit FROM projects ORDER BY id LIMIT 20"
        )
        out = dict(row)
        out["projects"] = [dict(p) for p in projects]
        out["last_updated"] = str(out.get("last_updated") or "")
        return jsonify({"success": True, "data": to_camel(out)})
    except Exception as e:
        return jsonify({"success": True, "data": {"totalReceived": 0, "totalSpent": 0, "pendingApproval": 0, "available": 0, "fiscalYear": "", "projects": []}})


@app.route("/api/projects/<project_id>/approve", methods=["POST"])
def approve_project(project_id):
    """Approve a project / budget item (sarpanch action)."""
    data = request.get_json() or {}
    user_id = data.get("user_id") or data.get("userId")
    if not user_id:
        return jsonify({"success": False, "error": "user_id required"}), 400
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "user_id must be numeric"}), 400

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, external_id, village_id, name, status, sanctioned FROM projects WHERE id::text = %s OR external_id = %s",
                    (str(project_id), str(project_id)),
                )
                proj = cur.fetchone()
                if not proj:
                    return jsonify({"success": False, "error": "Project not found"}), 404

                proj_id = proj["id"]
                village_id = proj.get("village_id")

                cur.execute(
                    "UPDATE projects SET status = %s WHERE id = %s",
                    ("approved", proj_id),
                )

                if village_id and proj.get("sanctioned") is not None:
                    # Update budget summary
                    cur.execute(
                        """
                        UPDATE budget_summary
                        SET pending_approval = GREATEST(0, pending_approval - COALESCE(%s,0)),
                            available = GREATEST(0, available - COALESCE(%s,0)),
                            total_spent = total_spent + COALESCE(%s,0)
                        WHERE village_id = %s
                        """,
                        (proj.get("sanctioned"), proj.get("sanctioned"), proj.get("sanctioned"), village_id),
                    )
                    
                    # Also update project's internal tracking
                    cur.execute(
                        """
                        UPDATE projects
                        SET released = COALESCE(released, 0) + COALESCE(%s,0),
                            spent = COALESCE(spent, 0) + COALESCE(%s,0)
                        WHERE id = %s
                        """,
                        (proj.get("sanctioned"), proj.get("sanctioned"), proj_id),
                    )

                cur.execute(
                    """
                    INSERT INTO activities (external_id, village_id, type, title, description, reference, icon)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        f"ACT-{proj['external_id']}",
                        village_id,
                        "approval",
                        "Budget / Project Approved",
                        f"Project '{proj['name']}' approved by user {user_id}.",
                        f"Project: {proj['external_id']}",
                        "task_alt",
                    ),
                )

                conn.commit()
        return jsonify({"success": True, "message": "Project approved"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------- Activities ----------
@app.route("/api/activities")
def list_activities():
    village_id = request.args.get("village_id", type=int)
    try:
        if village_id:
            rows = run_query(
                "SELECT id, external_id, type, title, description, reference, icon, created_at FROM activities WHERE village_id = %s ORDER BY created_at DESC LIMIT 20",
                (village_id,),
            )
        else:
            rows = run_query(
                "SELECT id, external_id, type, title, description, reference, icon, created_at FROM activities ORDER BY created_at DESC LIMIT 20"
            )
        return jsonify({"success": True, "data": to_camel(rows)})
    except Exception:
        return jsonify({"success": True, "data": []})


# Custom query endpoint
@app.route("/api/query", methods=["GET", "POST"])
def run_custom_query():
    try:
        from queries import get_custom_result
        rows = get_custom_result()
        return jsonify({"success": True, "data": rows})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    from config import HOST, PORT, DEBUG
    app.run(host=HOST, port=PORT, debug=DEBUG)
