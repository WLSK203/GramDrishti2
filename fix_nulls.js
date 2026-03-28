const supabaseUrl = 'https://vikieodqlvvntnxbtapm.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZpa2llb2RxbHZ2bnRueGJ0YXBtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3MDk5OTksImV4cCI6MjA5MDI4NTk5OX0.fI-y-0NfMnBryD-ef7YFeW2t9RqvKq3zIRDvJl91ukI';

const options = {
  method: 'PATCH',
  headers: {
    'apikey': supabaseKey,
    'Authorization': `Bearer ${supabaseKey}`,
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
  },
  body: JSON.stringify({ village_id: 1 })
};

fetch(`${supabaseUrl}/rest/v1/users?village_id=is.null`, options)
.then(() => fetch(`${supabaseUrl}/rest/v1/issues?village_id=is.null`, options))
.then(() => console.log('Fixed DB nulls'))
.catch(console.error);
