const namesInput = document.querySelector('#names');
const groupCount = document.querySelector('#group-count');
const groupSize = document.querySelector('#group-size');
const matrixWrap = document.querySelector('#matrix-wrap');
const status = document.querySelector('#count-status');

function names() { return namesInput.value.split(/\r?\n/).map(v => v.trim()).filter(Boolean); }
function rebuild() {
  const people = names();
  const old = new Map([...document.querySelectorAll('[data-pair]')].map(el => [el.dataset.pair, el.value]));
  status.textContent = people.length ? `参加者 ${people.length}名 / 必要人数 ${Number(groupCount.value) * Number(groupSize.value)}名` : '';
  status.className = people.length === Number(groupCount.value) * Number(groupSize.value) ? 'status ok' : 'status warn';
  if (!people.length) { matrixWrap.innerHTML = '<p class="empty">参加者名を入力すると、相性表がここに表示されます。</p>'; return; }
  const table = document.createElement('table');
  const head = document.createElement('tr'); head.append(document.createElement('th'));
  people.forEach(p => { const th = document.createElement('th'); th.textContent = p; head.append(th); }); table.append(head);
  people.forEach((person, i) => { const row = document.createElement('tr'); const th = document.createElement('th'); th.textContent = person; row.append(th);
    people.forEach((_, j) => { const td = document.createElement('td'); const input = document.createElement('input'); input.type = 'number'; input.step = 'any';
      if (i >= j) { input.value = i === j ? '0' : '—'; input.disabled = true; }
      else { input.name = `pair_${i}_${j}`; input.dataset.pair = `${i}_${j}`; input.value = old.get(`${i}_${j}`) ?? '0'; }
      td.append(input); row.append(td); }); table.append(row); }); matrixWrap.replaceChildren(table);
}
[namesInput, groupCount, groupSize].forEach(el => el.addEventListener('input', rebuild));
document.querySelector('#sample').addEventListener('click', () => { namesInput.value = ['佐藤','鈴木','高橋','田中','伊藤','渡辺','山本','中村','小林'].join('\n'); groupCount.value = 3; groupSize.value = 3; rebuild(); const values=[4,-3,1,2,0,-2,3,1,2,5,-4,1,0,2,-1,3,2,-2,4,1,0,3,-3,2,1,-1,4,2,0,3,-2,5,-1,2,1,3]; document.querySelectorAll('[data-pair]').forEach((el,i)=>el.value=values[i]); });
rebuild();
