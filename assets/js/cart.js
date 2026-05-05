/* Carrito Caprichos de Lili → WhatsApp deeplink
   - Sin backend, todo en localStorage
   - Genera mensaje formateado y abre wa.me
*/

const WHATSAPP_NUMBER = '595985381866'; // TODO Roberto: reemplazar por tu número real (sin + ni espacios)
const STORAGE_KEY = 'caprichos_cart_v1';
const MIN_DAYS_AHEAD = 3;

// ---- estado ----
function getCart(){ try{ return JSON.parse(localStorage.getItem(STORAGE_KEY))||[] }catch(e){ return [] } }
function setCart(items){ localStorage.setItem(STORAGE_KEY, JSON.stringify(items)); renderAll(); }
function clearCart(){ localStorage.removeItem(STORAGE_KEY); renderAll(); }

function addItem(id, name, price){
  const cart = getCart();
  const existing = cart.find(i => i.id === id);
  if(existing){ existing.qty += 1; } else { cart.push({id, name, price, qty: 1}); }
  setCart(cart);
  flashCart();
}
function changeQty(id, delta){
  const cart = getCart();
  const item = cart.find(i => i.id === id);
  if(!item) return;
  item.qty += delta;
  const filtered = cart.filter(i => i.qty > 0);
  setCart(filtered);
}
function removeItem(id){ setCart(getCart().filter(i => i.id !== id)); }

function cartTotal(){ return getCart().reduce((s,i) => s + i.qty * i.price, 0); }
function cartCount(){ return getCart().reduce((s,i) => s + i.qty, 0); }

// ---- formateo ----
function fmtGs(n){ return 'Gs. ' + n.toLocaleString('es-PY'); }
function todayPlus(days){
  const d = new Date(); d.setDate(d.getDate() + days);
  return d.toISOString().split('T')[0];
}
function fmtFechaLarga(isoDate){
  if(!isoDate) return '';
  const d = new Date(isoDate + 'T12:00:00');
  return d.toLocaleDateString('es-PY', { weekday:'long', day:'numeric', month:'long', year:'numeric' });
}

// ---- render ----
function renderAll(){
  renderMiniCart();
  renderCartPanel();
}
function renderMiniCart(){
  const badge = document.getElementById('cart-badge');
  const total = document.getElementById('cart-total-mini');
  const count = cartCount();
  if(badge){ badge.textContent = count; badge.classList.toggle('hidden', count === 0); }
  if(total){ total.textContent = fmtGs(cartTotal()); }
  const fab = document.getElementById('cart-fab');
  if(fab){ fab.classList.toggle('hidden', count === 0); }
}
function renderCartPanel(){
  const list = document.getElementById('cart-items');
  const totalEl = document.getElementById('cart-total');
  const empty = document.getElementById('cart-empty');
  const checkout = document.getElementById('cart-checkout');
  if(!list) return;
  const cart = getCart();
  list.innerHTML = '';
  if(cart.length === 0){
    if(empty) empty.classList.remove('hidden');
    if(checkout) checkout.classList.add('hidden');
    if(totalEl) totalEl.textContent = fmtGs(0);
    return;
  }
  if(empty) empty.classList.add('hidden');
  if(checkout) checkout.classList.remove('hidden');
  cart.forEach(item => {
    const row = document.createElement('div');
    row.className = 'flex items-center justify-between gap-3 py-3 border-b border-stone-200';
    row.innerHTML = `
      <div class="flex-1 min-w-0">
        <p class="font-semibold truncate">${item.name}</p>
        <p class="text-sm text-stone-500">${fmtGs(item.price)} c/u</p>
      </div>
      <div class="flex items-center gap-2">
        <button data-action="dec" data-id="${item.id}" class="w-8 h-8 rounded-full border border-stone-300 hover:bg-stone-100">−</button>
        <span class="w-6 text-center font-semibold">${item.qty}</span>
        <button data-action="inc" data-id="${item.id}" class="w-8 h-8 rounded-full border border-stone-300 hover:bg-stone-100">+</button>
      </div>
      <p class="font-bold w-24 text-right">${fmtGs(item.qty * item.price)}</p>
      <button data-action="remove" data-id="${item.id}" class="text-stone-400 hover:text-brand-red text-xl leading-none">×</button>
    `;
    list.appendChild(row);
  });
  if(totalEl) totalEl.textContent = fmtGs(cartTotal());
}

// ---- abrir/cerrar panel ----
function openCart(){ document.getElementById('cart-panel')?.classList.remove('hidden'); document.body.style.overflow='hidden'; }
function closeCart(){ document.getElementById('cart-panel')?.classList.add('hidden'); document.body.style.overflow=''; }
function flashCart(){
  const fab = document.getElementById('cart-fab');
  if(!fab) return;
  fab.classList.add('animate-pulse');
  setTimeout(() => fab.classList.remove('animate-pulse'), 800);
}

// ---- envío a WhatsApp ----
function buildWhatsAppMessage(form){
  const cart = getCart();
  if(cart.length === 0) return null;
  const esRetiro = form.modalidad === 'Pasar a buscar';
  const lines = [];
  lines.push('🛒 *NUEVO PEDIDO — CAPRICHOS DE LILI*');
  lines.push('━━━━━━━━━━━━━━━━━━');
  lines.push(`👤 *Cliente:* ${form.nombre || '(sin nombre)'}`);
  if(form.telefono) lines.push(`📞 *Teléfono:* ${form.telefono}`);
  if(esRetiro){
    lines.push(`🏪 *Modalidad:* Pasar a buscar (retiro en local)`);
  } else {
    lines.push(`🚚 *Modalidad:* Envío a domicilio`);
    lines.push(`📍 *Zona:* ${form.zona || '(no indicada)'}`);
    if(form.direccion) lines.push(`🏠 *Dirección:* ${form.direccion}`);
  }
  lines.push(`📅 *${esRetiro ? 'Retiro' : 'Entrega'}:* ${fmtFechaLarga(form.fecha)}`);
  lines.push('━━━━━━━━━━━━━━━━━━');
  lines.push('*Pedido:*');
  cart.forEach(item => {
    lines.push(`• ${item.qty}× ${item.name} — ${fmtGs(item.qty * item.price)}`);
  });
  lines.push('━━━━━━━━━━━━━━━━━━');
  lines.push(`💰 *TOTAL:* ${fmtGs(cartTotal())}`);
  if(form.comentarios) lines.push(`📝 *Comentarios:* ${form.comentarios}`);
  lines.push('');
  lines.push('_Pedido generado desde caprichosdelili.com_');
  return lines.join('\n');
}

function sendOrder(){
  const form = {
    nombre: document.getElementById('f-nombre')?.value.trim(),
    telefono: document.getElementById('f-telefono')?.value.trim(),
    modalidad: document.getElementById('f-modalidad')?.value || 'Envío a domicilio',
    zona: document.getElementById('f-zona')?.value,
    direccion: document.getElementById('f-direccion')?.value.trim(),
    fecha: document.getElementById('f-fecha')?.value,
    comentarios: document.getElementById('f-comentarios')?.value.trim()
  };
  // validación mínima
  if(!form.nombre){ alert('Por favor ingresá tu nombre.'); return; }
  if(form.modalidad !== 'Pasar a buscar' && !form.zona){ alert('Por favor elegí zona de entrega.'); return; }
  if(!form.fecha){ alert('Por favor elegí fecha de entrega.'); return; }
  const minDate = todayPlus(MIN_DAYS_AHEAD);
  if(form.fecha < minDate){
    alert(`La fecha de entrega debe ser al menos ${MIN_DAYS_AHEAD} días después de hoy (mínimo: ${fmtFechaLarga(minDate)}).`);
    return;
  }
  const msg = buildWhatsAppMessage(form);
  if(!msg){ alert('Tu carrito está vacío.'); return; }
  const url = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(msg)}`;
  window.open(url, '_blank', 'noopener');
}

// ---- listeners delegados ----
document.addEventListener('click', (e) => {
  const t = e.target.closest('[data-action]');
  if(!t) return;
  const id = t.dataset.id;
  const action = t.dataset.action;
  if(action === 'add'){
    addItem(id, t.dataset.name, parseInt(t.dataset.price, 10));
  } else if(action === 'inc'){ changeQty(id, +1);
  } else if(action === 'dec'){ changeQty(id, -1);
  } else if(action === 'remove'){ removeItem(id);
  } else if(action === 'open-cart'){ openCart();
  } else if(action === 'close-cart'){ closeCart();
  } else if(action === 'send-order'){ sendOrder();
  } else if(action === 'clear-cart'){ if(confirm('¿Vaciar el carrito?')) clearCart();
  }
});

// ---- toggle modalidad envío/retiro ----
function toggleModalidad(){
  const modalidad = document.getElementById('f-modalidad')?.value;
  const campoZona = document.getElementById('campo-zona');
  const campoDireccion = document.getElementById('campo-direccion');
  const esRetiro = modalidad === 'Pasar a buscar';
  if(campoZona) campoZona.classList.toggle('hidden', esRetiro);
  if(campoDireccion) campoDireccion.classList.toggle('hidden', esRetiro);
}

// ---- init ----
document.addEventListener('DOMContentLoaded', () => {
  // setear min de fecha
  const fechaInput = document.getElementById('f-fecha');
  if(fechaInput){
    fechaInput.min = todayPlus(MIN_DAYS_AHEAD);
  }
  // listener para toggle modalidad
  const modalidadSelect = document.getElementById('f-modalidad');
  if(modalidadSelect){
    modalidadSelect.addEventListener('change', toggleModalidad);
    toggleModalidad();
  }
  renderAll();
});
