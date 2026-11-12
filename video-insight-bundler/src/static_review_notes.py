"""Explicit, user-triggered note downloads for offline review (no autosave)."""


def notes_panel() -> str:
    return """<section><h2>Save your review notes</h2>
<p role="note"><strong>Static package: notes and checkboxes are not saved automatically.</strong>
Download your notes before closing or refreshing this page. Keep the downloaded file with your handoff.</p>
<label for="review-notes">Decision, evidence checked, open risks, and recommended next action</label>
<textarea id="review-notes" style="display:block;width:95%;min-height:180px"></textarea>
<button type="button" id="save-notes">Download review notes</button><p id="notes-status" aria-live="polite"></p>
<details id="notes-export-panel"><summary>Exported notes JSON (manual-save fallback)</summary><pre id="notes-export" style="white-space:pre-wrap"></pre></details>
<script>document.getElementById('save-notes').addEventListener('click',()=>{
const notes={page:document.title,saved_at:new Date().toISOString(),notes:document.getElementById('review-notes').value,
checklist:Array.from(document.querySelectorAll('input[type=checkbox]')).map(n=>({item:n.parentElement.textContent.trim(),completed:n.checked}))};
const payload=JSON.stringify(notes,null,2);
document.getElementById('notes-export').textContent=payload;
document.getElementById('notes-export-panel').open=true;
const url=URL.createObjectURL(new Blob([payload],{type:'application/json'}));
const link=document.createElement('a');link.href=url;link.download='review-notes.json';link.click();
setTimeout(()=>URL.revokeObjectURL(url),1000);
document.getElementById('notes-status').textContent='Download requested. Confirm the file is saved before leaving. If your browser does not save it, copy the exported JSON below into an external file.';
});</script></section>"""
