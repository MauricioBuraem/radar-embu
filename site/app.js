/* Radar Embu — interface. Lê window.RX (gerado por `python -m coletor.site`).
   item: [id, codigo, texto, aaaammdd, grupo, situacao, [idx vereadores], tema, fase] */
(function(){
const D=window.RX, V=D.v, IT=D.items;
const nf=n=>Number(n).toLocaleString('pt-BR');
const MES=['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez'];
const dt=s=>{s=String(s).replace(/-/g,'');return `${+s.slice(6,8)} ${MES[+s.slice(4,6)-1]} ${s.slice(0,4)}`};
const mesAno=s=>{s=String(s).replace(/-/g,'');return `${MES[+s.slice(4,6)-1]} ${s.slice(0,4)}`};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
/* links vindos dos dados: só https (bloqueia javascript: e afins, mesmo se o sistema da Câmara for adulterado) */
const url=s=>/^https:\/\//i.test(String(s??''))?esc(s):'#';
const mail=s=>/^[^\s@<>"']+@[^\s@<>"']+$/.test(String(s??''))?esc(s):'';
const norm=s=>String(s).normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase();
const $=id=>document.getElementById(id);
const svg=(p,s=22)=>`<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${p}</svg>`;
const ICON={
 pin:'<path d="M12 21s7-6.2 7-11a7 7 0 10-14 0c0 4.8 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/>',
 ask:'<path d="M21 12a8 8 0 01-11.8 7L4 20l1.2-4.4A8 8 0 1121 12z"/><path d="M9.8 9.5a2.3 2.3 0 114 1.6c-.7.6-1.3 1-1.3 1.9"/><path d="M12.5 16h.01"/>',
 medal:'<circle cx="12" cy="14" r="5"/><path d="M9 9.5L6.5 3h4L12 6.5 13.5 3h4L15 9.5"/>',
 law:'<path d="M7 3h8l4 4v14H7z"/><path d="M15 3v4h4M10 12h6M10 16h6"/>',
 dots:'<circle cx="6" cy="12" r="1.4"/><circle cx="12" cy="12" r="1.4"/><circle cx="18" cy="12" r="1.4"/>',
 road:'<path d="M8 3L4 21M16 3l4 18M12 4v3M12 11v3M12 18v3"/>',
 leaf:'<path d="M5 19c0-9 5-14 15-14 0 10-5 15-14 14z"/><path d="M5 19c3-4 6-7 10-9"/>',
 bulb:'<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 00-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0012 3z"/>',
 sign:'<path d="M12 3l9 16H3z"/><path d="M12 10v4M12 17h.01"/>',
 walk:'<path d="M3 20h18M5 20v-4h4v4M10 16v-5h4v9M15 11V7h4v13"/>',
 tree:'<path d="M12 21v-7"/><path d="M12 14a5 5 0 01-4-8 4.5 4.5 0 018 0 5 5 0 01-4 8z"/><path d="M6 21h12"/>',
 cross:'<path d="M9 3h6v6h6v6h-6v6H9v-6H3V9h6z"/>',
 book:'<path d="M4 5a2 2 0 012-2h13v16H6a2 2 0 00-2 2z"/><path d="M4 21V5M9 7h6"/>',
 shield:'<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
 drop:'<path d="M12 3s6 6.5 6 11a6 6 0 01-12 0c0-4.5 6-11 6-11z"/>',
 bus:'<rect x="4" y="4" width="16" height="13" rx="2"/><path d="M4 11h16M8 17v3M16 17v3M8 14h.01M16 14h.01"/>',
 heart:'<path d="M12 20s-7-4.5-7-10a4 4 0 017-2.6A4 4 0 0119 10c0 5.5-7 10-7 10z"/>',
 star:'<path d="M12 3l2.7 5.6 6.1.8-4.5 4.2 1.2 6-5.5-3-5.5 3 1.2-6L3.2 9.4l6.1-.8z"/>',
 cal:'<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 10h16M8 3v4M16 3v4"/>',
 flag:'<path d="M5 21V4M5 4h11l-2 4 2 4H5"/>',
 vote:'<path d="M4 13l4 4L20 5"/>'
};
const CAT={
 b:['Pedidos para os bairros','Asfalto, poda, iluminação, lombada, praça. É um pedido à Prefeitura, que decide se faz.','pin','Pedido'],
 c:['Cobranças e perguntas','Requerimentos de informação à Prefeitura e pedidos a outros órgãos.','ask','Cobrança'],
 h:['Homenagens','Moções de aplauso e de pesar, títulos de cidadão, nomes de rua e datas comemorativas.','medal','Homenagem'],
 l:['Propostas de lei','Projetos que criam regra, programa ou obrigação na cidade.','law','Proposta de lei'],
 o:['Outros','Emendas ao orçamento, vetos, moções de apoio ou repúdio e regras internas da Câmara.','dots','Outro']};
const ORDER=['b','c','h','l','o'];
const TH={luz:['Iluminação','bulb'],asf:['Asfalto e buracos','road'],tra:['Trânsito','sign'],agu:['Água e esgoto','drop'],
 lim:['Limpeza e poda','leaf'],cal:['Calçadas','walk'],laz:['Praças e lazer','tree'],sau:['Saúde','cross'],
 edu:['Escolas','book'],seg:['Segurança','shield'],bus:['Ônibus','bus'],
 pes:['Votos de pesar','heart'],tit:['Títulos e medalhas','star'],nom:['Nomes de rua e prédio','flag'],dat:['Datas comemorativas','cal'],par:['Aplausos e parabéns','medal']};
const THH=[['pes',/pesar|falecimento/],['tit',/titulo|medalha|comenda|diploma|honra/],['nom',/denomina|da nome/],
 ['dat',/institui o dia|institui a semana|dia municipal|semana municipal|calendario|data comemorativa|institui o mes/],['par',/./]];
const TEMA_MSG={luz:'iluminação',asf:'conserto de asfalto',tra:'melhoria no trânsito',agu:'água e esgoto',lim:'limpeza e poda',cal:'conserto de calçada',laz:'melhoria em praça e área de lazer',sau:'melhoria na saúde',edu:'melhoria em escola',seg:'segurança',bus:'melhoria no transporte'};

IT.forEach(it=>{it.n=norm(it[2]+' '+it[1]); it.th=it[7]||''; if(it[4]==='h'){const t=THH.find(([,rx])=>rx.test(it.n)); it.th=t?t[0]:''}});
const hue=i=>(i*53+18)%360;
const ini=s=>{const w=s.replace(/^(Professora|Professor|Dr\.?|Dra\.?)\s+/i,'').split(/\s+/).filter(x=>!/^(da|de|do|dos|das|e)$/i.test(x));return ((w[0]||'?')[0]+(w.length>1?w[w.length-1][0]:'')).toUpperCase()};
V.forEach(v=>{v.in=ini(v.ap)});
const av=i=>V[i].foto?`<img class="av" src="fotos/${esc(V[i].id)}.jpg" alt="" loading="lazy">`:`<span class="av" style="background:hsl(${hue(i)} 70% 90%);color:hsl(${hue(i)} 55% 28%)" aria-hidden="true">${esc(V[i].in)}</span>`;
const reduce=matchMedia('(prefers-reduced-motion:reduce)').matches;
const HOJE=new Date().toISOString().slice(0,10);

/* ---------- cartão de proposta ---------- */
function stt(r){if(!r)return'';const k=/aprovad|sancionad|promulgad|lid[ao]|encaminhad/i.test(r)?'ok':/rejeit|arquivad/i.test(r)?'no':'';return `<span class="stt ${k}">${esc(r)}</span>`}
function itemHTML(it,showAut){
  const c=it[4], t=TH[it.th], icon=t?t[1]:CAT[c][2];
  const aut=it[6];
  const who=showAut&&aut.length?`<span class="who">${aut.slice(0,3).map(a=>av(a)+`<span class="n">${esc(V[a].ap)}</span>`).join('')}${aut.length>3?`<span class="mute">+${aut.length-3}</span>`:''}</span>`:'<span></span>';
  return `<li class="it k-${c}"><span class="ic">${svg(ICON[icon])}</span><div>
    <p class="tx">${esc(it[2])}</p>
    <div class="mt"><span class="lab">${t?esc(t[0]):CAT[c][3]}</span>${stt(it[5])}<span>${dt(it[3])}</span><span>·</span><span>${esc(it[1])}</span></div>
    <div class="ft">${who}<a class="ext" href="https://nopapercloud.cmembu.sp.gov.br/spl/processo.aspx?id=${esc(it[0])}" target="_blank" rel="noopener">Ver na Câmara ↗</a></div></div></li>`;
}
function pager(host,items,showAut,step){
  let n=0; host.innerHTML='<ul class="items"></ul>';
  const ul=host.firstChild, btn=document.createElement('button');
  btn.className='more'; btn.type='button';
  const add=()=>{ul.insertAdjacentHTML('beforeend',items.slice(n,n+step).map(i=>itemHTML(i,showAut)).join(''));n+=step;
    if(n>=items.length)btn.remove();else btn.textContent=`Mostrar mais ${Math.min(step,items.length-n)} (faltam ${nf(items.length-n)})`};
  btn.addEventListener('click',add); if(items.length>step)host.appendChild(btn); add();
}
function themeCount(items){const m=new Map();items.forEach(it=>{if(it.th)m.set(it.th,(m.get(it.th)||0)+1)});return [...m.entries()].sort((a,b)=>b[1]-a[1])}

/* ---------- painel ---------- */
const sheet=$('sheet'), veil=$('veil'); let lastFocus=null;
function openSheet(k,icon,title,sub){
  lastFocus=document.activeElement; $('sh-top').className='sh-top k-'+k; $('sh-i').innerHTML=svg(ICON[icon],24);
  $('sh-t').textContent=title; $('sh-s').textContent=sub||''; $('sh-f').innerHTML=''; $('sh-f').style.display='none'; $('sh-b').innerHTML=''; $('sh-b').scrollTop=0;
  sheet.classList.add('on'); veil.classList.add('on'); document.body.style.overflow='hidden'; $('sh-x').focus();
}
function closeSheet(){sheet.classList.remove('on');veil.classList.remove('on');document.body.style.overflow='';if(lastFocus)lastFocus.focus()}
$('sh-x').addEventListener('click',closeSheet); veil.addEventListener('click',closeSheet);
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&sheet.classList.contains('on'))closeSheet()});
function openCat(c,vi){
  const all=IT.filter(it=>it[4]===c&&(vi==null||it[6].includes(vi)));
  openSheet(c,CAT[c][2],CAT[c][0],`${nf(all.length)} ${vi==null?'de todos os vereadores':'de '+V[vi].ap} desde a posse`);
  const th=themeCount(all); let cur='';
  const draw=()=>pager($('sh-b'),cur?all.filter(it=>it.th===cur):all,vi==null,20);
  if(th.length>1){
    $('sh-f').style.display='';
    $('sh-f').innerHTML=`<ul class="chips"><li><button class="chip on" type="button" data-t="">Tudo<small>${nf(all.length)}</small></button></li>${th.map(([k,n])=>`<li><button class="chip" type="button" data-t="${k}">${esc(TH[k][0])}<small>${nf(n)}</small></button></li>`).join('')}</ul>`;
    $('sh-f').onclick=e=>{const b=e.target.closest('[data-t]');if(!b)return;cur=b.dataset.t;$('sh-f').querySelectorAll('.chip').forEach(x=>x.classList.toggle('on',x===b));$('sh-b').scrollTop=0;draw()};
  }
  draw();
}
function openNaos(vi){
  const v=V[vi];
  openSheet('o','sign',`Quando ${v.ap} não votou “sim”`,`${v.naos.length} ${v.naos.length===1?'votação':'votações'} desde a posse`);
  $('sh-b').innerHTML='<ul class="items">'+v.naos.map(n=>`<li class="it k-o"><span class="ic">${svg(ICON.sign)}</span><div><p class="tx">${esc(n.t)}</p>
    <div class="mt"><span class="stt ${n.v==='nao'?'no':''}">${n.v==='nao'?'Votou não':'Absteve-se'}</span>${n.r?`<span>Resultado: ${esc(n.r.toLowerCase())}</span>`:''}<span>·</span><span>${dt(n.d)}</span></div>
    <div class="ft"><span class="mute">${esc(n.m||'')}</span>${n.u?`<a class="ext" href="${url(n.u)}" target="_blank" rel="noopener">Ver na Câmara ↗</a>`:''}</div></div></li>`).join('')+'</ul>';
}

/* ---------- topo ---------- */
function countUp(el,to){ if(reduce){el.textContent=nf(to);return} const t0=performance.now(),from=Math.round(to*.8);
  const step=t=>{const p=Math.min(1,(t-t0)/900),e=1-Math.pow(1-p,3);el.textContent=nf(Math.round(from+(to-from)*e));if(p<1)requestAnimationFrame(step)};requestAnimationFrame(step)}
const STATS=[['',IT.length,'propostas desde a posse','#fff'],['b',D.catot.b||0,'pedidos para os bairros','#7fd3d8'],['h',D.catot.h||0,'homenagens','#f39ac1'],['l',D.catot.l||0,'propostas de lei','#8fd49a']];
$('stats').innerHTML=STATS.map(([k,n,l,c],i)=>`<div class="stat"><b id="st${i}" style="color:${c}">${nf(n)}</b><span>${l}</span></div>`).join('');
STATS.forEach(([,n],i)=>countUp($('st'+i),n));
const cad=D.cadeiras||21;
if(D.sal&&D.sal.v){
  const POSSE=new Date(D.posse+'T00:00:00-03:00').getTime(), POR_MS=cad*D.sal.v*12/(365.25*864e5);
  const brl=new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'});
  $('ml').textContent=`Salário pago aos ${cad} vereadores desde a posse`;
  $('ms').textContent=`e subindo agora · estimativa: ${cad} salários de ${brl.format(D.sal.v)} por mês desde 1º de janeiro de 2025, sem 13º e férias`;
  const tick=()=>{$('tick').textContent=brl.format((Date.now()-POSSE)*POR_MS)};
  tick(); if(!reduce)setInterval(tick,120);
}else{ document.querySelector('.meter').style.display='none' }
const GER=new Date(D.gerh);
function ago(){ const m=Math.max(0,Math.round((Date.now()-GER.getTime())/6e4));
  const q=m<2?'agora mesmo':m<60?`há ${m} minutos`:m<120?'há 1 hora':m<1440?`há ${Math.floor(m/60)} horas`:m<2880?'ontem':`há ${Math.floor(m/1440)} dias`;
  $('livet').textContent=`Ao vivo · conferido ${q}`;
  $('upd').textContent=`Última leitura no sistema da Câmara: ${GER.toLocaleDateString('pt-BR',{day:'numeric',month:'long'})} às ${GER.toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'})}. O robô volta lá duas vezes por dia.`}
ago(); setInterval(ago,6e4);

/* ---------- pedidos repetidos ---------- */
D.rep.forEach((g,i)=>{g.i=i;g.items=g.ids.map(n=>IT[n]).filter(Boolean)});
const repHTML=g=>`<button class="rp" type="button" data-g="${g.i}"><span class="rn num">${g.n}<small>vezes</small></span>
  <span class="rr">${esc(g.r)}</span><span class="rb">${esc(g.b||'Embu das Artes')}</span>
  <span class="rm"><span class="lab k-b" style="background:var(--b-t);color:var(--b)">${esc((TH[g.th]||['Pedido'])[0])}</span><span>${g.a} ${g.a===1?'vereador pediu':'vereadores pediram'}</span><span>·</span><span>de ${mesAno(g.d0)} a ${mesAno(g.d1)}</span></span><span class="go">Ver os pedidos e cobrar →</span></button>`;
const SITE=/^https?:/.test(location.protocol)?location.origin+location.pathname:'https://radarembu.org/';
/* A Câmara não publica WhatsApp dos gabinetes: a cobrança por WhatsApp vai para a Central de Notícias, que leva ao vereador. */
const CENTRAL_WA='5511916492207';
const waCentral=(ap,txt)=>`Olá, Central de Notícias! Sou morador de Embu das Artes e peço que vocês cobrem ${ap} sobre este problema. Segue a mensagem:\n\n${txt}`;
function openRep(g){
  openSheet('b',(TH[g.th]||['','pin'])[1],g.r,`${(TH[g.th]||['Pedido'])[0]} · pedido ${g.n} vezes${g.b?' · '+g.b:''}`);
  const cnt=new Map(); g.items.forEach(it=>it[6].forEach(a=>cnt.set(a,(cnt.get(a)||0)+1)));
  const who=[...cnt.entries()].sort((a,b)=>b[1]-a[1]);
  const msg=a=>`Olá, ${V[a].ap}. Sou morador de Embu das Artes. A Câmara já recebeu ${g.n} pedidos de ${TEMA_MSG[g.th]||'melhoria'} para a ${g.r}${g.b?', no '+g.b:''}, desde ${mesAno(g.d0)}. ${cnt.get(a)===1?'Um deles saiu':cnt.get(a)+' deles saíram'} do seu gabinete, e o problema continua. O que a Prefeitura respondeu? O que ainda pode ser feito?\n\nFonte: ${SITE}`;
  $('sh-b').innerHTML=`${who.length?`<div class="cob"><h3>Cobre uma resposta</h3>
    <p>A mensagem já vem pronta. Escolha o vereador, ajuste o texto se quiser e envie.</p>
    <label class="field" for="cob-v">Para quem
      <select id="cob-v">${who.map(([a,n])=>`<option value="${a}">${esc(V[a].ap)} (${n} ${n===1?'pedido':'pedidos'} para esta rua)</option>`).join('')}</select></label>
    <label class="field" for="cob-t">Mensagem<textarea id="cob-t"></textarea></label>
    <div class="acts" id="cob-a"></div><div class="ct" id="cob-c"></div></div>`:''}
    <p class="h3">Os ${g.n} pedidos, do mais recente ao mais antigo</p><div id="replist"></div>`;
  if(who.length){
    const sel=$('cob-v'), ta=$('cob-t');
    const links=()=>{const v=V[+sel.value], t=encodeURIComponent(ta.value);
      $('cob-a').innerHTML=(v.email?`<a class="btn br" href="mailto:${mail(v.email)}?subject=${encodeURIComponent(g.r+': o problema continua')}&body=${t}">Enviar por e-mail</a>`:'')
        +`<a class="btn wa" href="https://wa.me/${CENTRAL_WA}?text=${encodeURIComponent(waCentral(v.ap,ta.value))}" target="_blank" rel="noopener">Pedir cobrança no WhatsApp</a>`;
      $('cob-c').innerHTML=`O WhatsApp vai para a <b>Central de Notícias</b> (11 91649-2207), que leva a cobrança a ${esc(v.ap)}.<br>`+[v.email?`E-mail oficial: <b>${esc(v.email)}</b>`:'',v.tel?`Telefone do gabinete: <b>${esc(v.tel)}</b>`:''].filter(Boolean).join(' · ')
        +(v.email?'':`${v.tel?'<br>':''}A Câmara não publica e-mail deste gabinete. ${v.url?`<a href="${url(v.url)}" target="_blank" rel="noopener">Use o formulário “Fale com o vereador” ↗</a>`:''}`);};
    const fill=()=>{ta.value=msg(+sel.value);links()};
    sel.addEventListener('change',fill); ta.addEventListener('input',links); fill();
  }
  pager($('replist'),g.items,true,20);
}
document.addEventListener('click',e=>{const b=e.target.closest('[data-g]');if(b)openRep(D.rep[+b.dataset.g])});
(function(){ let n=0; const host=$('reps'), btn=document.createElement('button'); btn.className='more'; btn.type='button'; btn.style.gridColumn='1/-1';
  const add=()=>{host.insertAdjacentHTML('beforeend',D.rep.slice(n,n+9).map(repHTML).join(''));n+=9;host.appendChild(btn);
    if(n>=D.rep.length)btn.remove();else btn.textContent=`Mostrar mais ruas (${D.rep.length-n} na fila)`};
  btn.addEventListener('click',()=>{btn.remove();add()});
  if(!D.rep.length)host.innerHTML='<p class="mute">Nenhuma rua com pedido repetido ainda.</p>'; else add(); })();

/* ---------- bairro ---------- */
$('bl').innerHTML=D.bairros.slice(0,200).map(b=>`<option value="${esc(b)}"></option>`).join('');
$('chips').innerHTML=D.bairros.slice(0,10).map(b=>`<li><button class="chip" type="button" data-b="${esc(b)}">${esc(b)}</button></li>`).join('');
function bairro(q){
  const host=$('bres'), k=norm(q.trim()), city=k.length===0;
  $('chips').querySelectorAll('.chip').forEach(x=>x.classList.toggle('on',norm(x.dataset.b)===k));
  if(!city&&k.length<3){host.innerHTML='<div class="panel"><p class="mute" style="margin:0">Continue digitando: são precisas pelo menos 3 letras.</p></div>';return}
  const items=city?IT:IT.filter(it=>it.n.includes(k));
  if(!items.length){host.innerHTML=`<div class="panel"><p class="mute" style="margin:0">Nada encontrado para “${esc(q)}”. Confira a grafia ou tente só uma parte do nome.</p></div>`;return}
  const cnt=new Map(); items.forEach(it=>it[6].forEach(a=>cnt.set(a,(cnt.get(a)||0)+1)));
  const top=[...cnt.entries()].sort((a,b)=>b[1]-a[1]), mx=top.length?top[0][1]:1;
  const th=themeCount(items.filter(it=>it[4]==='b'||it[4]==='c')).slice(0,5);
  const reps=city?[]:D.rep.filter(g=>g.items.some(it=>it.n.includes(k))).slice(0,3);
  host.innerHTML=`<div class="panel">
   <div class="ph"><span class="big num">${nf(items.length)}</span><p>${city?'propostas para <b>a cidade inteira</b> desde a posse':`${items.length===1?'proposta cita':'propostas citam'} <b>${esc(q.trim())}</b>`}</p></div>
   <div class="two">
     ${top.length?`<div><h3 class="h3">${city?'Quem mais propôs':'Quem mais pediu'}</h3><ol class="rank">${top.slice(0,5).map(([a,n])=>`<li>${av(a)}<span class="nm">${esc(V[a].ap)} <span class="mute" style="font-weight:400">· ${esc(V[a].part)}</span></span><b class="num">${nf(n)}</b><span class="br"><i style="width:${n/mx*100}%"></i></span></li>`).join('')}</ol>
       ${top.length>5?`<p class="note">${city?`Os outros ${top.length-5} estão nas fichas, mais abaixo.`:`Mais ${top.length-5} vereadores também citaram.`}</p>`:''}</div>`:''}
     ${th.length?`<div><h3 class="h3">O que mais pedem</h3><ul class="themes">${th.map(([t,n])=>`<li><span class="ti">${svg(ICON[TH[t][1]],18)}</span><span>${esc(TH[t][0])}</span><b class="num">${nf(n)}</b></li>`).join('')}</ul></div>`:''}
     ${city?`<div><h3 class="h3">Bairros mais citados</h3><ul class="themes">${D.bairros.slice(0,5).map((b,i)=>`<li><span class="ti">${svg(ICON.pin,18)}</span><button class="lnk" type="button" data-b="${esc(b)}">${esc(b)}</button><b class="num">${nf(D.bairrosn[i])}</b></li>`).join('')}</ul></div>`:''}
   </div>
   ${reps.length?`<p class="h3" style="margin-top:24px">Pedidos que voltam por aqui</p><div class="reps">${reps.map(repHTML).join('')}</div>`:''}
   <p class="h3" style="margin-top:24px">${city?'As propostas mais recentes':'Os pedidos mais recentes'}</p><div id="blist"></div></div>`;
  pager($('blist'),items,true,4);
}
let bt; $('bq').addEventListener('input',e=>{clearTimeout(bt);bt=setTimeout(()=>bairro(e.target.value),120)});
document.addEventListener('click',e=>{const b=e.target.closest('[data-b]');if(b){$('bq').value=b.dataset.b;bairro(b.dataset.b);$('bq').scrollIntoView({block:'center',behavior:reduce?'auto':'smooth'})}});
bairro('');

/* ---------- trabalho ou homenagem ---------- */
const tot=ORDER.reduce((s,c)=>s+(D.catot[c]||0),0);
const pctTrab=Math.round(((D.catot.b||0)+(D.catot.c||0)+(D.catot.l||0))/tot*100);
$('hsub').textContent=`São ${nf(tot)} propostas desde a posse. ${pctTrab} de cada 100 são pedidos, cobranças ou propostas de lei; ${Math.round((D.catot.h||0)/tot*100)} são homenagens. Toque num grupo para ler cada uma.`;
$('split').innerHTML=ORDER.map(c=>`<i class="k-${c}" style="flex:${D.catot[c]||0} 1 0"></i>`).join('');
$('cats').innerHTML=ORDER.map(c=>`<button class="cat k-${c}" type="button" data-c="${c}"><span class="ci">${svg(ICON[CAT[c][2]],26)}</span><span class="cv num">${nf(D.catot[c]||0)}</span><span class="cn">${CAT[c][0]}</span><span class="cd">${CAT[c][1]}</span><span class="go">Ver todas →</span></button>`).join('');
$('cats').addEventListener('click',e=>{const b=e.target.closest('[data-c]');if(b)openCat(b.dataset.c,null)});

/* ---------- fichas ---------- */
const temVot=D.nvot>0;
const nEx=V.filter(v=>v.ex).length;
$('vsub').textContent=temVot?`${nEx} vereadores em exercício hoje. Em ${Math.floor(D.unan/D.nvot*100)} de cada 100 votações nominais, ninguém votou diferente. Toque nos números da ficha para ver os detalhes.`:`Toque nos números da ficha para ver os detalhes.`;
if(!nEx){$('quem').value='todos'}
[...new Set(V.map(v=>v.part).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'pt')).forEach(p=>{const o=document.createElement('option');o.value=p;o.textContent=`${p} (${V.filter(v=>v.part===p).length})`;$('partido').appendChild(o)});
function ring(v){
  const t=v.S||0, C=2*Math.PI*30;
  if(!t)return `<div class="ring"><svg width="76" height="76" viewBox="0 0 76 76" aria-hidden="true"><circle cx="38" cy="38" r="30" fill="none" stroke="#eceef0" stroke-width="9"/></svg><b class="num">–</b></div>`;
  const seg=(n,col,off)=>n?`<circle cx="38" cy="38" r="30" fill="none" stroke="${col}" stroke-width="9" stroke-dasharray="${n/t*C} ${C}" stroke-dashoffset="${-off/t*C}" transform="rotate(-90 38 38)"/>`:'';
  return `<div class="ring"><svg width="76" height="76" viewBox="0 0 76 76" role="img" aria-label="${v.P} presenças em ${t} sessões"><circle cx="38" cy="38" r="30" fill="none" stroke="#eceef0" stroke-width="9"/>${seg(v.P,'#111418',0)}${seg(v.F,'#c6382b',v.P)}</svg><b class="num">${Math.round(v.P/t*100)}%</b></div>`;
}
function card(v){
  const i=V.indexOf(v);
  const pres=v.S?`<p><b class="num">${v.P} de ${v.S}</b> sessões com presença<small class="num"><b class="${v.F?'bad':''}">${v.F} ${v.F===1?'ausência registrada':'ausências registradas'}</b></small></p>`:`<p class="mute">Sem sessão registrada no período.</p>`;
  return `<article class="card">
   <div class="ch">
     <div class="idr">${v.foto?`<img class="pho" src="fotos/${esc(v.id)}.jpg" alt="Foto de ${esc(v.ap)}" loading="lazy">`:`<div class="pho" aria-hidden="true">${esc(v.in)}</div>`}<div><h3>${esc(v.ap)}</h3>${v.nome&&norm(v.nome)!==norm(v.ap)?`<p class="civil">${esc(v.nome)}</p>`:''}</div></div>
     <div class="tags">${v.part?`<span class="pill">${esc(v.part)}</span>`:''}${v.mesa?`<span class="pill r">${esc(v.mesa)}${v.mesa_fim&&v.mesa_fim<HOJE?` até ${mesAno(v.mesa_fim)}`:''}</span>`:''}${v.ex?'':'<span class="pill r">Fora do cargo hoje</span>'}${v.sf?'<span class="pill r">Sem ficha no site da Câmara</span>':''}</div></div>
   <div class="cb">
     ${temVot?`<div class="pres">${ring(v)}${pres}</div>`:''}
     <div class="mini num"><div><b>${D.sal&&D.sal.v?'R$ '+nf(Math.round(D.sal.v)):'–'}</b><span>salário por mês</span></div><div><b>${nf(Object.values(v.cat).reduce((a,b)=>a+b,0))}</b><span>propostas desde a posse</span></div></div>
     <div><p class="h3">O que propôs</p>
       <div class="bar5" aria-hidden="true">${ORDER.map(c=>v.cat[c]?`<i class="k-${c}" style="flex:${v.cat[c]} 1 0"></i>`:'').join('')}</div>
       ${ORDER.map(c=>`<button class="pick k-${c} num" type="button" data-v="${i}" data-c="${c}" ${v.cat[c]?'':'disabled'}><i></i><span>${CAT[c][0]}</span><b>${nf(v.cat[c])}</b><span class="ar" aria-hidden="true">›</span></button>`).join('')}</div>
     ${temVot?`<div><p class="h3">Como votou</p>
       <div class="vote num"><div><b>${nf(v.vs)}</b><span>vezes sim</span></div><div class="n"><b>${nf(v.vn+v.va)}</b><span>${v.va?'não ou abstenção':'vezes não'}</span></div></div>
       ${/^presidente/i.test(v.mesa)?'<p class="note">Quem preside a sessão normalmente só vota para desempatar.</p>':''}
       ${v.naos.length?`<p style="margin:10px 0 0"><button class="lnk" type="button" data-n="${i}">Ver quando não votou sim →</button></p>`:''}</div>`:''}
     ${v.url?`<p class="foot"><a href="${url(v.url)}" target="_blank" rel="noopener">Ficha oficial na Câmara ↗</a>${v.email?` · <a href="mailto:${mail(v.email)}">${esc(v.email)}</a>`:''}</p>`:''}
   </div></article>`;
}
const ORD={nome:(a,b)=>a.ap.localeCompare(b.ap,'pt'),faltas:(a,b)=>(b.F-a.F),l:(a,b)=>b.cat.l-a.cat.l,h:(a,b)=>b.cat.h-a.cat.h,b:(a,b)=>b.cat.b-a.cat.b,nao:(a,b)=>(b.vn+b.va)-(a.vn+a.va)};
function render(){
  const q=norm($('q').value.trim()),p=$('partido').value,o=$('ordem').value,todos=$('quem').value==='todos';
  const base=V.filter(v=>todos||v.ex);
  const L=base.filter(v=>(!p||v.part===p)&&(!q||norm(v.ap+' '+v.nome).includes(q))).sort((a,b)=>ORD[o](a,b)||ORD.nome(a,b));
  $('grid').innerHTML=L.length?L.map(card).join(''):'<p class="mute">Nenhum vereador com esse filtro. Apague a busca ou escolha “Todos”.</p>';
  $('conta').textContent=L.length===base.length?`Mostrando ${base.length} vereadores${todos?' (inclui quem já deixou o cargo)':''}.`:`Mostrando ${L.length} de ${base.length} vereadores.`;
}
['q','partido','ordem','quem'].forEach(id=>$(id).addEventListener('input',render));
$('grid').addEventListener('click',e=>{
  const p=e.target.closest('.pick'); if(p&&!p.disabled){openCat(p.dataset.c,+p.dataset.v);return}
  const n=e.target.closest('[data-n]'); if(n)openNaos(+n.dataset.n)});
render();

/* ---------- método ---------- */
$('m-pres').textContent=temVot?`Lida do relatório do painel eletrônico de cada sessão (${D.sess} sessões até ${dt(D.ult)}). Conta como presente quem aparece como “Presente” ou votou em alguma votação da sessão, porque o relatório marca “---” até para quem votou.${D.semreg.length?` ${D.semreg.length} sessões ficaram de fora por não terem relatório legível.`:''}`:'Ainda sem relatórios de sessão coletados.';
$('m-vot').textContent=temVot?`Só entram votações nominais do painel eletrônico: ${nf(D.nvot)} desde a posse. Em ${nf(D.unan)} delas, todos os que votaram escolheram a mesma opção.`:'Ainda sem votações coletadas.';
$('m-sal').innerHTML=D.sal&&D.sal.v?`Subsídio de R$ ${D.sal.v.toLocaleString('pt-BR',{minimumFractionDigits:2})} por mês para a legislatura 2025–2028, aprovado pela Câmara em outubro de 2022 (<a href="${url(D.sal.u)}" target="_blank" rel="noopener">${esc(D.sal.fonte)}</a>). O contador é uma estimativa: ${cad} salários brutos por mês desde a posse, sem 13º nem férias.`:'Valor ainda não confirmado.';
})();
