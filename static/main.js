const uploadForm = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const uploadUsername = document.getElementById('uploadUsername');
const statusP = document.getElementById('status');
const annotatedWrapper = document.getElementById('annotatedWrapper');
const facesWrapper = document.getElementById('facesWrapper');

uploadForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const file = fileInput.files[0];
  if (!file) return alert('pick an image first');
  statusP.textContent = 'Uploading...';

  const fd = new FormData();
  fd.append('image', file);
  fd.append('username', uploadUsername.value || '');

  const res = await fetch('/detect', { method: 'POST', body: fd });
  const data = await res.json();
  handleResult(data);
});

function handleResult(data) {
  if (!data || data.status !== 'ok') {
    statusP.textContent = 'Error: ' + (data?.message || 'unknown');
    return;
  }
  statusP.textContent = `Faces found: ${data.count} — saved: ${data.saved}`;
  annotatedWrapper.innerHTML = `<img src="${data.annotated}" alt="annotated">`;
  facesWrapper.innerHTML = '';
  data.faces.forEach((f) => {
    const img = document.createElement('img');
    img.src = f;
    facesWrapper.appendChild(img);
  });
}

/* ----- webcam capture ----- */
const video = document.getElementById('video');
const captureBtn = document.getElementById('captureBtn');
const camUsername = document.getElementById('camUsername');

async function startCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;
  } catch (err) {
    console.error('camera error', err);
    statusP.textContent = 'Cannot access camera: ' + err.message;
  }
}
startCamera();

captureBtn.addEventListener('click', async () => {
  // capture current frame
  const canvas = document.createElement('canvas');
  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  const dataUrl = canvas.toDataURL('image/jpeg');

  statusP.textContent = 'Sending snapshot...';

  const payload = {
    imageBase64: dataUrl,
    username: camUsername.value || ''
  };

  const res = await fetch('/detect', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  handleResult(data);
});
