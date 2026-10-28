const namesInput = document.querySelector('#names');
const participantCount = document.querySelector('#participant-count');
const groupCount = document.querySelector('#group-count');
const groupSizesContainer = document.querySelector('#group-sizes');
const matrixWrap = document.querySelector('#matrix-wrap');
const initialForm = JSON.parse(document.querySelector('#initial-form').textContent);
const pairValues = new Map(Object.entries(initialForm).filter(([key]) => key.startsWith('pair_')).map(([key, value]) => [key, value[0]]));
let currentSizes = initialForm.group_sizes?.map(Number) ?? [];
let lastPeople = '';

function names() { return namesInput.value.split(/\r?\n/).map(value => value.trim()).filter(Boolean); }
function mode() { return document.querySelector('[name="allocation_mode"]:checked').value; }
function balancedSizes(total, count) {
  const base = Math.floor(total / count);
  const extra = total % count;
  return Array.from({ length: count }, (_, index) => base + (index >= count - extra ? 1 : 0));
}
function validCounts() {
  const total = Number(participantCount.value);
  const count = Number(groupCount.value);
  return Number.isInteger(total) && total >= 2 && total <= 60 && Number.isInteger(count) && count >= 1 && count <= total;
}
function updateSummary() {
  const total = Number(participantCount.value);
  const count = Number(groupCount.value);
  const suppliedNames = names();
  const namedCountOK = suppliedNames.length === 0 || suppliedNames.length === total;
  const uniqueNames = new Set(suppliedNames).size === suppliedNames.length;
  const countsOK = validCounts();
  const sizesOK = currentSizes.length === count && currentSizes.every(size => Number.isInteger(size) && size > 0) && currentSizes.reduce((a, b) => a + b, 0) === total;
  const valid = countsOK && sizesOK && namedCountOK && uniqueNames;
  const description = document.querySelector('#allocation-description');
  description.textContent = countsOK ? `${total}人 → ${count}班（${currentSizes.map(size => `${size || 0}人`).join('・')}）` : '参加者数と班数を確認してください';
  const message = document.querySelector('#count-status');
  if (!countsOK) message.textContent = '参加者は2〜60人、班数は1以上・参加者数以下にしてください。';
  else if (!sizesOK) message.textContent = `各班の合計 ${currentSizes.reduce((a, b) => a + b, 0)}人 / 参加者 ${total}人。合計を合わせてください。`;
  else message.textContent = '✓ 全員を、上の人数で班分けします';
  document.querySelector('#allocation-summary').classList.toggle('invalid', !countsOK || !sizesOK);
  const namesStatus = document.querySelector('#names-status');
  namesStatus.textContent = !suppliedNames.length ? `名前の入力なし：参加者1〜${total || '…'}を使用します` : !uniqueNames ? '参加者名が重複しています。別の名前またはIDを使ってください。' : `${suppliedNames.length}人分の名前 / 設定 ${total}人${namedCountOK ? ' ✓' : '：人数を合わせてください'}`;
  namesStatus.className = namedCountOK && uniqueNames ? 'status ok' : 'status warn';
  document.querySelector('#run-button').disabled = !valid;
  document.querySelector('#submit-status').textContent = valid ? description.textContent : '上の人数・班の設定や参加者名を確認してください。';
}
function renderSizes() {
  groupCount.max = participantCount.value || 60;
  if (!validCounts()) { currentSizes = []; groupSizesContainer.replaceChildren(); updateSummary(); return; }
  const count = Number(groupCount.value);
  if (mode() === 'auto' || currentSizes.length !== count) currentSizes = balancedSizes(Number(participantCount.value), count);
  const fields = currentSizes.map((size, index) => {
    const label = document.createElement('label'); label.textContent = `班 ${index + 1}`;
    const control = document.createElement('div'); control.className = 'number-with-unit';
    const input = document.createElement('input');
    input.type = 'number'; input.name = 'group_sizes'; input.min = '1'; input.max = participantCount.value; input.required = true; input.value = size;
    input.readOnly = mode() === 'auto'; input.setAttribute('aria-label', `班${index + 1}の人数`);
    input.addEventListener('input', () => { currentSizes[index] = Number(input.value); updateSummary(); });
    const unit = document.createElement('span'); unit.textContent = '人';
    control.append(input, unit); label.append(control); return label;
  }); groupSizesContainer.replaceChildren(...fields); updateSummary();
}
function rebuildMatrix() {
  const total = Number(participantCount.value);
  if (!Number.isInteger(total) || total < 2 || total > 60) { matrixWrap.replaceChildren(); lastPeople = ''; return; }
  const suppliedNames = names();
  const people = Array.from({ length: total }, (_, index) => suppliedNames[index] || `参加者${index + 1}`);
  const signature = JSON.stringify(people);
  if (signature === lastPeople) return;
  lastPeople = signature;
  const table = document.createElement('table'); table.setAttribute('aria-label', '参加者同士の相性行列');
  const head = document.createElement('tr'); head.append(document.createElement('th'));
  people.forEach(person => { const th = document.createElement('th'); th.textContent = person; th.scope = 'col'; head.append(th); }); table.append(head);
  people.forEach((person, i) => {
    const row = document.createElement('tr'); const th = document.createElement('th'); th.textContent = person; th.scope = 'row'; row.append(th);
    people.forEach((other, j) => {
      const td = document.createElement('td');
      if (i >= j) { td.className = 'derived-cell'; td.textContent = i === j ? '0' : (pairValues.get(`pair_${j}_${i}`) || '0'); td.dataset.mirror = `${j}_${i}`; }
      else {
        const input = document.createElement('input'); input.type = 'number'; input.step = 'any';
        input.name = `pair_${i}_${j}`; input.dataset.pair = `${i}_${j}`; input.value = pairValues.get(input.name) ?? '0';
        input.setAttribute('aria-label', `${person}と${other}の相性`);
        input.addEventListener('input', () => { pairValues.set(input.name, input.value); matrixWrap.querySelector(`[data-mirror="${i}_${j}"]`).textContent = input.value || '0'; }); td.append(input);
      } row.append(td);
    }); table.append(row);
  }); matrixWrap.replaceChildren(table);
}
participantCount.addEventListener('input', () => { renderSizes(); rebuildMatrix(); });
groupCount.addEventListener('input', () => renderSizes());
document.querySelectorAll('[name="allocation_mode"]').forEach(input => input.addEventListener('change', () => renderSizes()));
namesInput.addEventListener('input', () => { updateSummary(); rebuildMatrix(); });
document.querySelector('#sample').addEventListener('click', () => {
  namesInput.value = ['佐藤','鈴木','高橋','田中','伊藤','渡辺','山本','中村','小林'].join('\n'); participantCount.value = 9; groupCount.value = 3;
  document.querySelector('[name="allocation_mode"][value="auto"]').checked = true;
  pairValues.clear(); lastPeople = ''; renderSizes(); rebuildMatrix();
  const values = [4,-3,1,2,0,-2,3,1,2,5,-4,1,0,2,-1,3,2,-2,4,1,0,3,-3,2,1,-1,4,2,0,3,-2,5,-1,2,1,3];
  document.querySelectorAll('[data-pair]').forEach((input, index) => { input.value = values[index]; input.dispatchEvent(new Event('input')); });
});
document.querySelector('#ga-form').addEventListener('submit', event => {
  updateSummary();
  if (document.querySelector('#run-button').disabled) { event.preventDefault(); return; }
  document.querySelector('#run-button').textContent = '班分けを計算しています…';
});
renderSizes(); rebuildMatrix();
