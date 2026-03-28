const supabaseUrl = 'https://vikieodqlvvntnxbtapm.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZpa2llb2RxbHZ2bnRueGJ0YXBtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3MDk5OTksImV4cCI6MjA5MDI4NTk5OX0.fI-y-0NfMnBryD-ef7YFeW2t9RqvKq3zIRDvJl91ukI';

fetch(`${supabaseUrl}/rest/v1/users?select=id,name,village_id`, {
  headers: {
    'apikey': supabaseKey,
    'Authorization': `Bearer ${supabaseKey}`
  }
})
.then(res => res.json())
.then(data => console.log(JSON.stringify(data, null, 2)))
.catch(err => console.error(err));
