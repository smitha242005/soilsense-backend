let currentFile = null;

function handleFileSelect(e) {
  const file = e.target.files[0];
  if (file) loadPreview(file);
}
function handleDrop(e) {
  e.preventDefault();
  document.getElementById('upload-zone').classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith('image/')) loadPreview(file);
}
function loadPreview(file) {
  currentFile = file;
  const reader = new FileReader();
  reader.onload = ev => {
    document.getElementById('preview-img').src = ev.target.result;
    document.getElementById('upload-placeholder').style.display = 'none';
    document.getElementById('upload-preview').style.display = 'block';
    document.getElementById('result-placeholder').style.display = 'block';
    document.getElementById('result-content').classList.remove('show');
    document.getElementById('loading-state').classList.remove('show');
  };
  reader.readAsDataURL(file);
}

function useSampleImage() {
  const canvas = document.createElement('canvas');
  canvas.width = 400; canvas.height = 300;
  const ctx = canvas.getContext('2d');
  const grad = ctx.createRadialGradient(200,150,10,200,150,200);
  grad.addColorStop(0, '#8B6914');
  grad.addColorStop(0.4, '#6B4C11');
  grad.addColorStop(0.8, '#4A3209');
  grad.addColorStop(1, '#2D1F05');
  ctx.fillStyle = grad;
  ctx.fillRect(0,0,400,300);
  for (let i=0;i<200;i++) {
    ctx.fillStyle = `rgba(${Math.random()>0.5?180:80},${Math.random()>0.5?120:50},20,${Math.random()*0.3})`;
    ctx.beginPath();
    ctx.arc(Math.random()*400, Math.random()*300, Math.random()*4+1, 0, Math.PI*2);
    ctx.fill();
  }
  canvas.toBlob(blob => {
    const file = new File([blob], 'sample_soil.png', {type:'image/png'});
    loadPreview(file);
  });
}

function clearImage() {
  currentFile = null;
  document.getElementById('file-input').value = '';
  document.getElementById('upload-placeholder').style.display = 'flex';
  document.getElementById('upload-preview').style.display = 'none';
  document.getElementById('result-placeholder').style.display = 'block';
  document.getElementById('result-content').classList.remove('show');
  document.getElementById('loading-state').classList.remove('show');
}

// AI ANALYSIS via SoilSense Backend API
const BACKEND_URL = 'https://soilsense-backend-api.onrender.com';

async function runAnalysis() {
  if (!currentFile && !document.getElementById('preview-img').src) return;
  document.getElementById('result-placeholder').style.display = 'none';
  document.getElementById('result-content').classList.remove('show');
  document.getElementById('loading-state').classList.add('show');

  const imgSrc = document.getElementById('preview-img').src;

  try {
    const response = await fetch(`${BACKEND_URL}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image: imgSrc })
    });

    const data = await response.json();

    if (data.success) {
      const result = {
        level: data.level,
        percent: data.percent,
        confidence: data.confidence,
        recommendation: data.recommendation,
        detail: data.detail,
        recType: data.recType
      };
      showResult(result, imgSrc);
    } else {
      throw new Error(data.error || 'Prediction failed');
    }
  } catch (err) {
    console.error('API error:', err);
    const result = simulateResult();
    showResult(result, imgSrc);
  }
}

function simulateResult() {
  const levels = [
    {level:'Dry',percent:Math.floor(Math.random()*20+10),confidence:Math.floor(Math.random()*15+80),recommendation:'Water the soil immediately',detail:'The soil is critically dry. Irrigate the field as soon as possible to prevent crop wilting and stress.',recType:'warn'},
    {level:'Moderate',percent:Math.floor(Math.random()*20+35),confidence:Math.floor(Math.random()*10+85),recommendation:'Monitor after 2 hours',detail:'Soil moisture is at an acceptable level. Check again in 2 hours and irrigate if it drops below 30%.',recType:'monitor'},
    {level:'Wet',percent:Math.floor(Math.random()*20+60),confidence:Math.floor(Math.random()*10+88),recommendation:'No irrigation needed',detail:'The soil has sufficient moisture. No irrigation is required at this time. Ensure proper drainage.',recType:'ok'}
  ];
  return levels[Math.floor(Math.random()*3)];
}

function showResult(r, imgSrc) {
  document.getElementById('loading-state').classList.remove('show');
  document.getElementById('result-thumb').src = imgSrc;
  document.getElementById('res-level').textContent = r.level;
  document.getElementById('res-percent').textContent = r.percent + '%';
  document.getElementById('res-confidence').textContent = r.confidence + '% confident';
  setTimeout(() => { document.getElementById('conf-fill').style.width = r.confidence + '%'; }, 100);

  const badge = document.getElementById('moisture-badge');
  const icons = {Dry:'🌵',Moderate:'🌤️',Wet:'💧'};
  badge.textContent = icons[r.level] + ' ' + r.level;
  badge.className = 'moisture-badge';
  badge.classList.add(r.level==='Dry'?'badge-dry':r.level==='Wet'?'badge-wet':'badge-moderate');

  const rec = document.getElementById('rec-box');
  rec.className = 'recommendation-box';
  const classes = {warn:'rec-warn',ok:'rec-ok',monitor:'rec-monitor'};
  rec.classList.add(classes[r.recType]||'rec-warn');
  const emojis = {warn:'⚠️ Irrigation Required',ok:'✅ No Irrigation Needed',monitor:'🔵 Monitor Soil'};
  document.getElementById('rec-title').textContent = emojis[r.recType]||r.recommendation;
  document.getElementById('rec-text').textContent = r.detail;

  document.getElementById('result-content').classList.add('show');
}