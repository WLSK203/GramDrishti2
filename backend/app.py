import os


from flask import Flask, jsonify, request
from flask_cors import CORS

from config import SECRET_KEY, CORS_ORIGINS
from database import get_connection, run_query, run_query_one

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
CORS(app, origins=CORS_ORIGINS, supports_credentials=True)

UPLOAD_FOLDER = "Uploaded data"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file found"}), 400

    file = request.files["file"]
    project_id = request.form.get("project_id")

    if file.filename == "":
        return jsonify({"success": False, "message": "Empty filename"}), 400

    if not project_id:
        save_dir = UPLOAD_FOLDER
        url_prefix = "/api/uploads/"
    else:
        try:
            project_id = int(project_id)
            project = run_query_one("SELECT name FROM projects WHERE id = %s", (project_id,))
            if not project:
                return jsonify({"success": False, "message": "Project not found"}), 404
                
            import re
            safe_name = re.sub(r'[^A-Za-z0-9]', '_', project["name"])
            folder_name = f"Project_{project_id}_{safe_name}"
            save_dir = os.path.join(UPLOAD_FOLDER, folder_name)
            os.makedirs(save_dir, exist_ok=True)
            url_prefix = f"/api/uploads/{folder_name}/"
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    import uuid
    ext = os.path.splitext(file.filename)[1]
    unique_name = uuid.uuid4().hex[:12] + ext
    save_path = os.path.join(save_dir, unique_name)
    file.save(save_path)

    # Return a URL-friendly path
    file_url = url_prefix + unique_name
    return jsonify({
        "success": True,
        "message": "File uploaded successfully",
        "path": file_url,
        "filename": file.filename
    })


@app.route("/api/uploads/<path:filename>")
def serve_upload(filename):
    """Serve uploaded files."""
    from flask import send_from_directory
    return send_from_directory(os.path.abspath(UPLOAD_FOLDER), filename)


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
                           i.status, i.status_name, i.priority, i.department, i.reported_by_id, i.reported_by_name, i.reported_date,
                           i.votes, i.location, COALESCE(p.progress, i.progress) as progress, i.contractor, i.estimated_cost, i.attachments, i.created_at,
                           p.verification_images,
                           EXISTS (SELECT 1 FROM issue_votes v WHERE v.issue_id = i.id AND v.user_id = %s) AS user_voted
                    FROM issues i
                    LEFT JOIN projects p ON p.id = i.project_id
                    WHERE i.village_id = %s
                    ORDER BY i.created_at DESC
                    LIMIT 50
                    """,
                    (user_id, village_id),
                )
            else:
                rows = run_query(
                    """
                    SELECT i.id, i.external_id, i.title, i.title_hindi, i.description, i.category, i.category_name,
                           i.status, i.status_name, i.priority, i.department, i.reported_by_id, i.reported_by_name, i.reported_date,
                           i.votes, i.location, COALESCE(p.progress, i.progress) as progress, i.contractor, i.estimated_cost, i.attachments, i.created_at,
                           p.verification_images,
                           false AS user_voted
                    FROM issues i
                    LEFT JOIN projects p ON p.id = i.project_id
                    WHERE i.village_id = %s
                    ORDER BY i.created_at DESC
                    LIMIT 50
                    """,
                    (village_id,),
                )
        else:
            rows = run_query(
                """
                SELECT i.id, i.external_id, i.title, i.title_hindi, i.description, i.category, i.category_name,
                       i.status, i.status_name, i.priority, i.department, i.reported_by_id, i.reported_by_name, i.reported_date,
                       i.votes, i.location, COALESCE(p.progress, i.progress) as progress, i.contractor, i.estimated_cost, i.attachments, i.created_at,
                       p.verification_images
                FROM issues i
                LEFT JOIN projects p ON p.id = i.project_id
                ORDER BY i.created_at DESC
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
        # Normalize for frontend — keep numeric id as numericId for delete operations
        import json as _json
        for r in rows:
            r["numeric_id"] = r["id"]
            r["id"] = r.get("external_id") or str(r["id"])
            # Parse attachments from JSON string to list
            att = r.get("attachments")
            if isinstance(att, str):
                try: r["attachments"] = _json.loads(att)
                except Exception: r["attachments"] = []
            elif att is None:
                r["attachments"] = []
                
            # Parse verification_images
            v_img = r.get("verification_images")
            if isinstance(v_img, str):
                try: r["verification_images"] = _json.loads(v_img)
                except Exception: r["verification_images"] = []
            elif v_img is None:
                r["verification_images"] = []
                
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
                reported_by_id, reported_by_name, reported_date, votes, location, attachments
            ) VALUES (%s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s, %s)
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
                __import__('json').dumps(data.get("attachments") or []),
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


# Delete an issue (only by the reporter)
@app.route("/api/issues/<issue_id>", methods=["DELETE"])
def delete_issue(issue_id):
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id") or data.get("userId") or request.args.get("user_id")

    if not user_id:
        return jsonify({"success": False, "error": "user_id is required"}), 400

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "user_id must be numeric"}), 400

    try:
        # Look up the issue — try numeric id first, then external_id
        issue = None
        try:
            numeric_id = int(issue_id)
            issue = run_query_one("SELECT id, reported_by_id FROM issues WHERE id = %s", (numeric_id,))
        except (TypeError, ValueError):
            pass

        if not issue:
            issue = run_query_one("SELECT id, reported_by_id FROM issues WHERE external_id = %s", (str(issue_id),))

        if not issue:
            return jsonify({"success": False, "error": "Issue not found (id=" + str(issue_id) + ")"}), 404

        if int(issue["reported_by_id"]) != int(user_id):
            return jsonify({"success": False, "error": "You can only delete your own issues"}), 403

        real_id = issue["id"]
        try:
            run_query("DELETE FROM issue_votes WHERE issue_id = %s", (real_id,), commit=True)
        except Exception:
            pass  # No votes to delete is fine
        run_query("DELETE FROM issues WHERE id = %s", (real_id,), commit=True)

        return jsonify({"success": True, "message": "Issue deleted successfully"})
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
            "SELECT id, external_id, name, sanctioned, released, spent, progress, status, contractor, category, start_date, deadline, completed_date, verifications_site_inspection, verifications_photos, verifications_materials, verifications_gps, verifications_community, verifications_audit, verification_images FROM projects WHERE village_id = %s ORDER BY id",
            (vid,),
        ) if vid else run_query(
            "SELECT id, external_id, name, sanctioned, released, spent, progress, status, contractor, category, start_date, deadline, completed_date, verifications_site_inspection, verifications_photos, verifications_materials, verifications_gps, verifications_community, verifications_audit, verification_images FROM projects ORDER BY id LIMIT 20"
        )
        
        import json as _json
        for p in projects:
            v_img = p.get("verification_images")
            if isinstance(v_img, str):
                try: p["verification_images"] = _json.loads(v_img)
                except: p["verification_images"] = []
            elif v_img is None:
                p["verification_images"] = []

        # Auto-recalculate total_spent and pending from actual project data
        real_spent = sum(float(p.get("spent", 0) or 0) for p in projects)
        real_pending = sum(
            max(0, float(p.get("sanctioned", 0) or 0) - float(p.get("spent", 0) or 0))
            for p in projects if str(p.get("status") or "").lower() not in ["completed", "closed", "resolved"]
        )
        real_sanctioned = sum(
            float(p.get("sanctioned", 0) or 0) 
            for p in projects if str(p.get("status") or "").lower() not in ["completed", "closed", "resolved"]
        )
        total_received = float(row.get("total_received", 0) or 0)

        out = dict(row)
        out["total_spent"] = real_spent
        out["pending_approval"] = real_pending
        out["sanctioned_funds"] = real_sanctioned
        out["available"] = total_received - real_spent - real_pending
        out["projects"] = [dict(p) for p in projects]
        out["last_updated"] = str(out.get("last_updated") or "")
        return jsonify({"success": True, "data": to_camel(out)})
    except Exception as e:
        return jsonify({"success": True, "data": {"totalReceived": 0, "totalSpent": 0, "pendingApproval": 0, "available": 0, "fiscalYear": "", "projects": []}})

@app.route("/api/projects", methods=["POST"])
def create_project():
    """Create a new project/budget item (admin/sarpanch action)."""
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    category = (data.get("category") or "other").strip()
    sanctioned = data.get("sanctioned")
    village_id = data.get("village_id") or data.get("villageId")
    
    if not name or sanctioned is None or not village_id:
        return jsonify({"success": False, "error": "Name, sanctioned amount, and village_id are required"}), 400
        
    try:
        sanctioned = float(sanctioned)
        village_id = int(village_id)
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "sanctioned must be a number and village_id must be an integer"}), 400

    from datetime import date
    import uuid
    external_id = f"PRJ-{uuid.uuid4().hex[:6].upper()}"
    start_date = date.today()
    status = "in_progress"

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Insert the project
                cur.execute(
                    """
                    INSERT INTO projects (
                        external_id, village_id, name, sanctioned, released, spent,
                        progress, status, start_date
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (external_id, village_id, name, sanctioned, 0, 0, 0, status, start_date)
                )
                proj_id = cur.fetchone()["id"]
                
                import re
                safe_name = re.sub(r'[^A-Za-z0-9]', '_', name)
                folder_path = os.path.join(UPLOAD_FOLDER, f"Project_{proj_id}_{safe_name}")
                os.makedirs(folder_path, exist_ok=True)
                
                # Update budget summary
                cur.execute(
                    """
                    UPDATE budget_summary
                    SET pending_approval = COALESCE(pending_approval, 0) + %s
                    WHERE village_id = %s
                    """,
                    (sanctioned, village_id)
                )
                
                # Log activity
                cur.execute(
                    """
                    INSERT INTO activities (external_id, village_id, type, title, description, reference, icon)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    ("ACT-" + external_id, village_id, "approval", "New Project Created", f"Project '{name}' was created.", f"Project: {external_id}", "add_circle_outline")
                )
                conn.commit()
                
                cur.execute(
                    "SELECT external_id, name, sanctioned, released, spent, progress, status, contractor, start_date, deadline, completed_date FROM projects WHERE id = %s",
                    (proj_id,)
                )
                new_proj = cur.fetchone()

        return jsonify({"success": True, "data": to_camel(dict(new_proj))}), 201
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/issues/<issue_id>/assign_contractor", methods=["POST"])
def assign_issue_to_contractor(issue_id):
    """Assign a complaint/issue to a contractor by creating a project from it."""
    data = request.get_json(silent=True) or {}
    contractor_name = data.get("contractor_name") or data.get("contractorName")
    user_id = data.get("user_id") or request.args.get("user_id")

    if not contractor_name:
        return jsonify({"success": False, "error": "contractor_name is required"}), 400

    try:
        # Look up the issue (by numeric id or external_id)
        issue = None
        try:
            issue = run_query_one("SELECT * FROM issues WHERE id = %s", (int(issue_id),))
        except (ValueError, TypeError):
            pass
        if not issue:
            issue = run_query_one("SELECT * FROM issues WHERE external_id = %s", (str(issue_id),))
        if not issue:
            return jsonify({"success": False, "error": "Issue not found"}), 404

        import uuid, datetime
        external_proj_id = "PRJ-" + uuid.uuid4().hex[:8].upper()
        village_id = issue["village_id"]
        
        # Determine sanctioned amount (either provided by frontend or fallback to category defaults)
        sanctioned_amount = data.get("sanctioned_amount")
        if sanctioned_amount is None:
            cat_to_sanctioned = {
                "water": 285000, "roads": 450000, "electricity": 175000,
                "sanitation": 120000, "education": 200000, "other": 150000
            }
            sanctioned_amount = cat_to_sanctioned.get((issue.get("category") or "other").lower(), 150000)
            
        sanctioned = float(sanctioned_amount)

        # Create project from issue
        row = run_query(
            """
            INSERT INTO projects (external_id, village_id, name, sanctioned, released, spent,
                progress, status, contractor, category, start_date, deadline)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                external_proj_id,
                village_id,
                issue["title"] or "Unnamed Project",
                sanctioned,
                0, 0, 0,
                "in_progress",
                contractor_name,
                issue.get("category") or "other",
                datetime.date.today(),
                datetime.date.today() + datetime.timedelta(days=90),
            ),
            commit=True
        )
        new_project = row[0] if row else None

        # Update issue status to in_progress, mark contractor, and link project
        run_query(
            "UPDATE issues SET status = 'in_progress', status_name = 'In Progress', contractor = %s, project_id = %s WHERE id = %s",
            (contractor_name, new_project["id"] if new_project else None, issue["id"]),
            commit=True
        )

        # Log activity
        try:
            run_query(
                "INSERT INTO activities (village_id, type, title, description, reference, icon) VALUES (%s,%s,%s,%s,%s,%s)",
                (village_id, "project_assigned", "Contractor Assigned",
                 f"Issue '{issue['title']}' assigned to {contractor_name}.",
                 external_proj_id, "engineering"),
                commit=True
            )
        except Exception:
            pass

        return jsonify({"success": True, "data": to_camel(dict(new_project)) if new_project else {}}), 201
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/projects/<project_id>/assign", methods=["POST"])
def assign_project(project_id):
    """Assign a contractor to a project."""
    data = request.get_json() or {}
    contractor_name = data.get("contractor_name")
    
    if not contractor_name:
        return jsonify({"success": False, "error": "contractor_name required"}), 400
        
    try:
        updated = run_query(
            "UPDATE projects SET contractor = %s, status = 'in_progress' WHERE id = %s RETURNING *",
            (contractor_name, project_id),
            commit=True
        )
        if not updated:
            return jsonify({"success": False, "error": "Project not found or could not be updated"}), 404
            
        project = updated[0]
        
        # Log activity
        run_query(
            "INSERT INTO activities (village_id, type, title, description, reference, icon) VALUES (%s, %s, %s, %s, %s, %s)",
            (
                project['village_id'], 'project_assigned', f"Contractor Assigned",
                f"Project '{project['name']}' assigned to {contractor_name}.",
                f"PRJ-{project_id}", 'engineering'
            ),
            commit=True
        )
        return jsonify({"success": True, "data": to_camel(dict(project))}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/projects/<project_id>/verify_step", methods=["POST"])
def verify_project_step(project_id):
    """Toggle a verification step for a project."""
    data = request.get_json() or {}
    step = data.get("step")
    photo_url = data.get("photo_url")
    
    valid_steps = [
        "verifications_site_inspection",
        "verifications_photos",
        "verifications_materials",
        "verifications_gps",
        "verifications_community",
        "verifications_audit"
    ]
    if step not in valid_steps:
        return jsonify({"success": False, "error": "Invalid verification step. Valid: " + str(valid_steps)}), 400
        
    try:
        # Fetch current project to get existing images
        curr_proj = run_query_one("SELECT verification_images FROM projects WHERE id = %s", (project_id,))
        if not curr_proj:
            return jsonify({"success": False, "error": "Project not found"}), 404
            
        import json
        images = []
        if curr_proj.get("verification_images"):
            try:
                images = curr_proj["verification_images"]
                if isinstance(images, str):
                    images = json.loads(images)
            except:
                pass
                
        if photo_url and photo_url not in images:
            images.append(photo_url)
            
        # Ensure the column exists (auto-migrate)
        try:
            run_query(f"ALTER TABLE projects ADD COLUMN IF NOT EXISTS {step} BOOLEAN DEFAULT FALSE", commit=True)
        except Exception:
            pass
            
        updated = run_query(
            f"UPDATE projects SET {step} = TRUE, verification_images = %s::jsonb WHERE id = %s RETURNING *",
            (json.dumps(images), project_id),
            commit=True
        )
        if not updated:
            return jsonify({"success": False, "error": "Project not found"}), 404
            
        project = updated[0]
        
        # Calculate new progress percentage
        completed_count = sum(1 for s in valid_steps if project.get(s) is True)
        progress_pct = round((completed_count / 6.0) * 100)
        status_update = ", status = 'completed', completed_date = CURRENT_DATE" if completed_count == 6 else ""
        
        # Save new progress to database
        updated_prog = run_query(
            f"UPDATE projects SET progress = %s{status_update} WHERE id = %s RETURNING *",
            (progress_pct, project_id),
            commit=True
        )
        if updated_prog:
            project = updated_prog[0]
            
        if completed_count == 6:
            run_query(
                "UPDATE issues SET status = 'resolved', status_name = 'Resolved / Completed' WHERE project_id = %s",
                (project_id,),
                commit=True
            )

        step_name = step.replace("verifications_", "").replace("_", " ").capitalize()
        
        run_query(
            "INSERT INTO activities (village_id, type, title, description, reference, icon) VALUES (%s, %s, %s, %s, %s, %s)",
            (
                project['village_id'], 'verification', f"Work Verified",
                f"Verification step '{step_name}' completed for project '{project['name']}'.",
                f"PRJ-{project_id}", 'verified'
            ),
            commit=True
        )
        
        return jsonify({"success": True, "data": to_camel(dict(project))}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

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

# ---------- Admin Panel ----------
@app.route("/api/admin/stats")
def admin_stats():
    """Get system-wide statistics for the admin dashboard."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Active villages
                cur.execute("SELECT COUNT(*) as count FROM villages")
                villages = cur.fetchone()["count"]
                
                # Registered users
                cur.execute("SELECT COUNT(*) as count FROM users")
                users = cur.fetchone()["count"]
                
                # Issues resolved
                cur.execute("SELECT COUNT(*) as count FROM issues WHERE status = 'resolved'")
                resolved = cur.fetchone()["count"]
                
                # Total funds tracked
                cur.execute("SELECT SUM(sanctioned) as total FROM projects")
                res = cur.fetchone()
                funds = float(res["total"] or 0)
                
                return jsonify({"success": True, "data": {
                    "activeVillages": villages,
                    "registeredUsers": users,
                    "issuesResolved": resolved,
                    "totalFundsTracked": funds
                }})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/admin/users")
def admin_users():
    """Get a list of all users for the admin directory."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT u.id, u.external_id, u.name, u.role, u.mobile, v.name as village_name 
                    FROM users u
                    LEFT JOIN villages v ON u.village_id = v.id
                    ORDER BY u.id DESC
                """)
                users = cur.fetchall()
                # Manually map role logic since to_camel doesn't format enums nicely
                return jsonify({"success": True, "data": to_camel(users)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/admin/alerts")
def admin_alerts():
    """Get recent high-priority activities or system alerts for admin."""
    try:
        # Reusing the existing activities log but limited to 'approval' or 'verification' roughly simulating alerts
        rows = run_query(
            "SELECT id, external_id, type, title, description, reference, icon, created_at FROM activities ORDER BY created_at DESC LIMIT 5"
        )
        return jsonify({"success": True, "data": to_camel(rows)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    from config import HOST, PORT, DEBUG
    app.run(host=HOST, port=PORT, debug=DEBUG)
