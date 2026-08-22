# core/web_server.py
import json
import os
import threading
from flask import Flask, render_template_string, request, jsonify
from werkzeug.serving import make_server

app = Flask(__name__)

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ERP Bot Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .table-responsive { max-height: 600px; }
        th { white-space: nowrap; }
    </style>
</head>
<body class="bg-light">
    <nav class="navbar navbar-dark bg-dark mb-4">
        <div class="container-fluid">
            <span class="navbar-brand mb-0 h1">🤖 ERP Automation Dashboard</span>
        </div>
    </nav>
    <div class="container-fluid px-4">
        <ul class="nav nav-tabs" id="myTab" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#stores">🏪 Store Manager</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" data-bs-toggle="tab" data-bs-target="#master">📦 Master Data</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" data-bs-toggle="tab" data-bs-target="#delays">⏱️ Step Delays</button>
            </li>
        </ul>
        <div class="tab-content bg-white p-4 border border-top-0 rounded-bottom shadow-sm" id="myTabContent">
            
            <!-- STORE MANAGER -->
            <div class="tab-pane fade show active" id="stores">
                <h4>Daftar Toko (Batch Mode)</h4>
                <div class="input-group mb-3 w-50">
                    <input type="text" id="newStoreName" class="form-control" placeholder="Nama Toko Baru">
                    <button class="btn btn-primary" onclick="addStore()">Tambah</button>
                </div>
                <ul class="list-group w-50" id="storeList"></ul>
            </div>

            <!-- MASTER DATA -->
            <div class="tab-pane fade" id="master">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h4>Master Data Barang</h4>
                    <button class="btn btn-warning fw-bold" onclick="openBatchModal()">🔄 Batch Update Terpilih</button>
                </div>
                <input type="text" id="searchItem" class="form-control mb-3" placeholder="🔍 Cari nama barang..." onkeyup="filterTable()">
                <div class="table-responsive border rounded">
                    <table class="table table-hover table-bordered mb-0" id="masterTable">
                        <thead class="table-dark sticky-top">
                            <tr>
                                <th width="40"><input type="checkbox" id="checkAll" onclick="toggleAll(this)"></th>
                                <th>Nama Barang</th>
                                <th>Harga Dasar</th>
                                <th>Diskon</th>
                                <th>Netto?</th>
                                <th>PPN?</th>
                                <th>Rules</th>
                                <th width="100">Aksi</th>
                            </tr>
                        </thead>
                        <tbody id="masterBody"></tbody>
                    </table>
                </div>
            </div>

            <!-- STEP DELAYS -->
            <div class="tab-pane fade" id="delays">
                <div class="alert alert-info">
                    <strong>Info:</strong> Atur jeda waktu (dalam detik) setelah bot melakukan aksi pada langkah tertentu. Kosongkan nilai delay untuk menggunakan nilai bawaan (Speed Profile default).
                </div>
                
                <div class="row">
                    <!-- PHASE 1 TABLE -->
                    <div class="col-md-6 mb-4">
                        <div class="card shadow-sm">
                            <div class="card-header bg-primary text-white fw-bold">
                                📋 Phase 1 & Reset Steps (coordinates.json)
                            </div>
                            <div class="card-body p-0">
                                <div class="table-responsive">
                                    <table class="table table-bordered table-hover mb-0">
                                        <thead class="table-light">
                                            <tr>
                                                <th>ID Langkah</th>
                                                <th>Aksi / Tipe</th>
                                                <th width="140">Delay (Detik)</th>
                                                <th width="80">Simpan</th>
                                            </tr>
                                        </thead>
                                        <tbody id="delayBodyPhase1"></tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- PHASE 2 TABLE -->
                    <div class="col-md-6 mb-4">
                        <div class="card shadow-sm">
                            <div class="card-header bg-success text-white fw-bold">
                                🔍 Phase 2, Save & Action Steps (coordinates_phase2.json)
                            </div>
                            <div class="card-body p-0">
                                <div class="table-responsive">
                                    <table class="table table-bordered table-hover mb-0">
                                        <thead class="table-light">
                                            <tr>
                                                <th>ID Langkah</th>
                                                <th>Aksi / Tipe</th>
                                                <th width="140">Delay (Detik)</th>
                                                <th width="80">Simpan</th>
                                            </tr>
                                        </thead>
                                        <tbody id="delayBodyPhase2"></tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

        </div>
    </div>

    <!-- BATCH UPDATE MODAL -->
    <div class="modal fade" id="batchModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header bg-warning">
                    <h5 class="modal-title fw-bold">Batch Update (<span id="selectedCount">0</span> item)</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="alert alert-info small">Kosongkan atau pilih "Jangan Ubah" pada kolom yang tidak ingin diupdate.</div>
                    <div class="mb-3">
                        <label class="fw-bold">Harga Baru</label>
                        <input type="number" id="batchPrice" class="form-control" placeholder="Kosongkan jika tidak diubah">
                    </div>
                    <div class="mb-3">
                        <label class="fw-bold">Diskon Baru</label>
                        <input type="text" id="batchDisc" class="form-control" placeholder="Contoh: 45,10,0,0 (Kosongkan jika tidak diubah)">
                    </div>
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <label class="fw-bold">Status Netto</label>
                            <select id="batchNetto" class="form-select">
                                <option value="">-- Jangan Ubah --</option>
                                <option value="true">Ya (Set Netto)</option>
                                <option value="false">Tidak (Reguler)</option>
                            </select>
                        </div>
                        <div class="col-md-6">
                            <label class="fw-bold">Status PPN</label>
                            <select id="batchTaxable" class="form-select">
                                <option value="">-- Jangan Ubah --</option>
                                <option value="true">Ya (Kena PPN)</option>
                                <option value="false">Tidak (Bebas PPN)</option>
                            </select>
                        </div>
                    </div>
                    <hr>
                    <!-- BATCH RULES -->
                    <div class="mb-2">
                        <label class="fw-bold text-primary">Aksi Price Rules Massal</label>
                        <select id="batchRuleAction" class="form-select border-primary" onchange="toggleBatchRuleInputs()">
                            <option value="IGNORE">-- Jangan Ubah Rule --</option>
                            <option value="UPDATE">✏️ Update / Set Rule Baru</option>
                            <option value="DELETE">🗑️ Hapus Semua Rule (Reset)</option>
                        </select>
                    </div>
                    <div id="batchRuleInputs" style="display: none;" class="p-3 bg-light border rounded">
                        <div class="mb-2">
                            <label>Logika (Kosongkan = Selalu Aktif / True)</label>
                            <input type="text" id="batchRuleLogic" class="form-control" placeholder="Otomatis 'True' jika dikosongkan">
                        </div>
                        <div class="row">
                            <div class="col-md-6">
                                <label>Diskon (%)</label>
                                <input type="number" id="batchRuleDisc" class="form-control" placeholder="0">
                            </div>
                            <div class="col-md-6">
                                <label>Mode Hitung</label>
                                <select id="batchRuleMode" class="form-select">
                                    <option value="NORMAL">NORMAL</option>
                                    <option value="FLAT_M2">FLAT M2</option>
                                    <option value="ALLOW_UPS">ALLOW UPS</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Batal</button>
                    <button type="button" class="btn btn-primary" onclick="applyBatchUpdate()">Simpan Perubahan</button>
                </div>
            </div>
        </div>
    </div>

    <!-- SINGLE EDIT MODAL -->
    <div class="modal fade" id="singleEditModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header bg-primary text-white">
                    <h5 class="modal-title fw-bold">Edit Barang</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <input type="hidden" id="editOriginalName">
                    <div class="mb-3">
                        <label class="fw-bold">Nama Barang</label>
                        <input type="text" id="editName" class="form-control" readonly disabled>
                    </div>
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <label class="fw-bold">Harga Dasar (Rp)</label>
                            <input type="number" id="editPrice" class="form-control">
                        </div>
                        <div class="col-md-6">
                            <label class="fw-bold">Diskon (Pisahkan koma)</label>
                            <input type="text" id="editDisc" class="form-control" placeholder="45,10,0,0">
                        </div>
                    </div>
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <div class="form-check form-switch">
                                <input class="form-check-input" type="checkbox" id="editNetto">
                                <label class="form-check-label fw-bold">Barang Netto (Tanpa Diskon Footer)</label>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-check form-switch">
                                <input class="form-check-input" type="checkbox" id="editTaxable">
                                <label class="form-check-label fw-bold">Kena PPN</label>
                            </div>
                        </div>
                    </div>
                    <hr>
                    <h6 class="fw-bold text-primary">📐 Price Rules (Logika Upselling / Diskon Khusus)</h6>
                    <div class="row mb-3">
                        <div class="col-md-5">
                            <label>Logika (Kosongkan = True)</label>
                            <div class="input-group">
                                <input type="text" id="editRuleLogic" class="form-control" placeholder="Otomatis 'True' jika kosong" oninput="markRuleActive()">
                                <button class="btn btn-outline-danger" type="button" onclick="clearSingleRule()" title="Hapus Rule Ini">🗑️</button>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <label>Diskon (%)</label>
                            <input type="number" id="editRuleDisc" class="form-control" placeholder="0" oninput="markRuleActive()">
                        </div>
                        <div class="col-md-4">
                            <label>Mode Hitung</label>
                            <select id="editRuleMode" class="form-select" onchange="markRuleActive()">
                                <option value="NORMAL">NORMAL</option>
                                <option value="FLAT_M2">FLAT M2</option>
                                <option value="ALLOW_UPS">ALLOW UPS (Upselling)</option>
                            </select>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Batal</button>
                    <button type="button" class="btn btn-primary" onclick="applySingleEdit()">Simpan Data</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // --- STORE LOGIC ---
        async function loadStores() {
            let res = await fetch('/api/stores');
            let stores = await res.json();
            let html = '';
            stores.forEach((s, i) => {
                html += `<li class="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                        <input class="form-check-input me-2" type="checkbox" ${s.selected ? 'checked' : ''} onchange="toggleStore('${s.name}', this.checked)">
                        ${s.name}
                    </div>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteStore('${s.name}')">Hapus</button>
                </li>`;
            });
            document.getElementById('storeList').innerHTML = html;
        }

        async function addStore() {
            let name = document.getElementById('newStoreName').value;
            if(!name) return;
            await fetch('/api/stores', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'add', name: name})
            });
            document.getElementById('newStoreName').value = '';
            loadStores();
        }

        async function deleteStore(name) {
            if(!confirm('Hapus toko ' + name + '?')) return;
            await fetch('/api/stores', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'delete', name: name})
            });
            loadStores();
        }

        async function toggleStore(name, checked) {
            await fetch('/api/stores', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'toggle', name: name, selected: checked})
            });
        }

        // --- MASTER DATA LOGIC ---
        let masterData = {};
        async function loadMaster() {
            let res = await fetch('/api/master');
            masterData = await res.json();
            renderMasterTable();
            filterTable();
        }

        function renderMasterTable() {
            let html = '';
            for(let key in masterData.items) {
                let item = masterData.items[key];
                let isTaxable = item.is_taxable !== false; 
                let ruleBadge = item.custom_rule ? `<span class="badge bg-info text-dark">${item.custom_rule.logic}</span>` : '-';
                
                html += `<tr>
                    <td><input type="checkbox" class="item-check" value="${key}"></td>
                    <td class="item-name fw-bold">${key}</td>
                    <td>Rp ${item.base_price.toLocaleString('id-ID')}</td>
                    <td>${item.default_discs.join(' + ')}%</td>
                    <td>${item.is_netto ? '✅' : '❌'}</td>
                    <td>${isTaxable ? '✅' : '❌'}</td>
                    <td>${ruleBadge}</td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="openSingleEdit('${key}')">✏️ Edit</button>
                    </td>
                </tr>`;
            }
            document.getElementById('masterBody').innerHTML = html;
        }

        function filterTable() {
            let input = document.getElementById("searchItem").value.toUpperCase();
            let tr = document.getElementById("masterBody").getElementsByTagName("tr");
            for (let i = 0; i < tr.length; i++) {
                let td = tr[i].getElementsByClassName("item-name")[0];
                if (td) {
                    let txtValue = td.textContent || td.innerText;
                    tr[i].style.display = txtValue.toUpperCase().indexOf(input) > -1 ? "" : "none";
                }
            }
        }

        function toggleAll(source) {
            let checkboxes = document.querySelectorAll('.item-check');
            checkboxes.forEach(cb => {
                if(cb.closest('tr').style.display !== 'none') cb.checked = source.checked;
            });
        }

        // --- BATCH UPDATE LOGIC ---
        function toggleBatchRuleInputs() {
            let action = document.getElementById('batchRuleAction').value;
            document.getElementById('batchRuleInputs').style.display = (action === 'UPDATE') ? 'block' : 'none';
        }

        function openBatchModal() {
            let selected = document.querySelectorAll('.item-check:checked');
            if(selected.length === 0) { alert("Pilih minimal 1 barang!"); return; }
            
            document.getElementById('batchPrice').value = '';
            document.getElementById('batchDisc').value = '';
            document.getElementById('batchNetto').value = '';
            document.getElementById('batchTaxable').value = '';
            
            document.getElementById('batchRuleAction').value = 'IGNORE';
            toggleBatchRuleInputs();
            document.getElementById('batchRuleLogic').value = '';
            document.getElementById('batchRuleDisc').value = '';
            document.getElementById('batchRuleMode').value = 'NORMAL';
            
            document.getElementById('selectedCount').innerText = selected.length;
            new bootstrap.Modal(document.getElementById('batchModal')).show();
        }

        async function applyBatchUpdate() {
            let selected = Array.from(document.querySelectorAll('.item-check:checked')).map(cb => cb.value);
            
            let price = document.getElementById('batchPrice').value;
            let disc = document.getElementById('batchDisc').value;
            let netto = document.getElementById('batchNetto').value;
            let taxable = document.getElementById('batchTaxable').value;

            let updates = {};
            if(price !== "") updates.base_price = parseFloat(price);
            if(disc !== "") updates.default_discs = disc.split(',').map(Number);
            if(netto !== "") updates.is_netto = (netto === "true");
            if(taxable !== "") updates.is_taxable = (taxable === "true");

            let ruleAction = document.getElementById('batchRuleAction').value;
            if (ruleAction === 'UPDATE') {
                let logic = document.getElementById('batchRuleLogic').value.trim();
                let mode = document.getElementById('batchRuleMode').value;
                let ruleDisc = parseFloat(document.getElementById('batchRuleDisc').value || 0);

                if (logic === "") logic = "True";

                updates.custom_rule = { logic: logic, disc: ruleDisc, mode: mode };
            } else if (ruleAction === 'DELETE') {
                updates.custom_rule = null;
            }

            if(Object.keys(updates).length === 0) {
                alert("Tidak ada data yang diubah!");
                return;
            }

            await fetch('/api/master/batch', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ keys: selected, updates: updates })
            });
            
            bootstrap.Modal.getInstance(document.getElementById('batchModal')).hide();
            loadMaster();
        }

        // --- SINGLE EDIT LOGIC ---
        let singleRuleActive = false;

        function markRuleActive() {
            singleRuleActive = true;
        }

        function clearSingleRule() {
            singleRuleActive = false;
            document.getElementById('editRuleLogic').value = '';
            document.getElementById('editRuleDisc').value = '';
            document.getElementById('editRuleMode').value = 'NORMAL';
        }

        function openSingleEdit(key) {
            let item = masterData.items[key];
            document.getElementById('editOriginalName').value = key;
            document.getElementById('editName').value = key;
            document.getElementById('editPrice').value = item.base_price;
            document.getElementById('editDisc').value = item.default_discs.join(',');
            document.getElementById('editNetto').checked = item.is_netto;
            document.getElementById('editTaxable').checked = item.is_taxable !== false;

            if(item.custom_rule) {
                singleRuleActive = true;
                document.getElementById('editRuleLogic').value = item.custom_rule.logic || '';
                document.getElementById('editRuleDisc').value = item.custom_rule.disc || 0;
                document.getElementById('editRuleMode').value = item.custom_rule.mode || 'NORMAL';
            } else {
                singleRuleActive = false;
                document.getElementById('editRuleLogic').value = '';
                document.getElementById('editRuleDisc').value = '';
                document.getElementById('editRuleMode').value = 'NORMAL';
            }

            new bootstrap.Modal(document.getElementById('singleEditModal')).show();
        }

        async function applySingleEdit() {
            let key = document.getElementById('editOriginalName').value;
            let payload = {
                base_price: parseFloat(document.getElementById('editPrice').value),
                default_discs: document.getElementById('editDisc').value.split(',').map(Number),
                is_netto: document.getElementById('editNetto').checked,
                is_taxable: document.getElementById('editTaxable').checked
            };

            if (singleRuleActive) {
                let ruleLogic = document.getElementById('editRuleLogic').value.trim();
                let ruleDisc = parseFloat(document.getElementById('editRuleDisc').value || 0);
                let ruleMode = document.getElementById('editRuleMode').value;

                if (ruleLogic === "") ruleLogic = "True";

                payload.custom_rule = { logic: ruleLogic, disc: ruleDisc, mode: ruleMode };
            } else {
                payload.custom_rule = null;
            }

            await fetch('/api/master/item', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ key: key, data: payload })
            });

            bootstrap.Modal.getInstance(document.getElementById('singleEditModal')).hide();
            loadMaster();
        }

        // --- STEP DELAYS LOGIC ---
        async function loadDelays() {
            let res = await fetch('/api/delays');
            let data = await res.json();
            
            renderDelayTable(data.phase1, 'delayBodyPhase1', 'phase1');
            renderDelayTable(data.phase2, 'delayBodyPhase2', 'phase2');
        }

        function renderDelayTable(coordsObj, tbodyId, phase) {
            let keys = Object.keys(coordsObj);
            
            // Sorting cerdas (numerik awalan & alfabet)
            keys.sort((a, b) => {
                let matchA = a.match(/^(\d+)_/);
                let matchB = b.match(/^(\d+)_/);
                
                if (matchA && matchB) {
                    return parseInt(matchA[1]) - parseInt(matchB[1]);
                } else if (matchA) {
                    return -1;
                } else if (matchB) {
                    return 1;
                } else {
                    return a.localeCompare(b);
                }
            });

            let html = '';
            keys.forEach(key => {
                let item = coordsObj[key];
                if(item && typeof item === 'object') {
                    let actionText = item.action || item.type || (item.value !== undefined ? 'HOTKEY/TEXT' : (item.x !== undefined ? 'CLICK' : 'AREA/BOX'));
                    actionText = String(actionText).toUpperCase();
                    let currentDelay = item.custom_delay !== undefined ? item.custom_delay : '';
                    
                    html += `<tr>
                        <td class="fw-bold small align-middle">${key}</td>
                        <td class="align-middle"><span class="badge bg-secondary">${actionText}</span></td>
                        <td>
                            <input type="number" step="0.1" class="form-control form-control-sm" id="delay_${phase}_${key}" value="${currentDelay}" placeholder="Default">
                        </td>
                        <td>
                            <button class="btn btn-sm btn-success w-100" onclick="saveDelay('${phase}', '${key}')">💾</button>
                        </td>
                    </tr>`;
                }
            });
            document.getElementById(tbodyId).innerHTML = html;
        }

        async function saveDelay(phase, stepId) {
            let val = document.getElementById(`delay_${phase}_${stepId}`).value;
            await fetch('/api/delays', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ phase: phase, step_id: stepId, custom_delay: val })
            });
            alert(`Delay untuk [${stepId}] berhasil disimpan!`);
        }

        window.onload = () => { loadStores(); loadMaster(); loadDelays(); };
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/stores', methods=['GET', 'POST'])
def api_stores():
    store_file = 'stores.json'
    stores = []
    if os.path.exists(store_file):
        with open(store_file, 'r') as f: stores = json.load(f)
    
    if request.method == 'POST':
        data = request.json
        if data['action'] == 'add':
            stores.append({"name": data['name'].upper(), "selected": True})
        elif data['action'] == 'delete':
            stores = [s for s in stores if s['name'] != data['name']]
        elif data['action'] == 'toggle':
            for s in stores:
                if s['name'] == data['name']: s['selected'] = data['selected']
        
        with open(store_file, 'w') as f: json.dump(stores, f, indent=4)
        return jsonify({"status": "ok"})
    
    return jsonify(stores)

@app.route('/api/master', methods=['GET'])
def api_master():
    master_file = 'master_data.json'
    if os.path.exists(master_file):
        with open(master_file, 'r') as f: return jsonify(json.load(f))
    return jsonify({"items": {}, "rules": {}})

@app.route('/api/master/batch', methods=['POST'])
def api_master_batch():
    data = request.json
    keys = data.get('keys', [])
    updates = data.get('updates', {}) 
    
    master_file = 'master_data.json'
    with open(master_file, 'r') as f: db = json.load(f)
    
    for key in keys:
        if key in db['items']:
            for u_key, u_val in updates.items():
                if u_key == 'custom_rule':
                    if u_val is None:
                        if 'custom_rule' in db['items'][key]:
                            del db['items'][key]['custom_rule']
                    else:
                        db['items'][key]['custom_rule'] = u_val
                else:
                    db['items'][key][u_key] = u_val
            
    with open(master_file, 'w') as f: json.dump(db, f, indent=4)
    return jsonify({"status": "ok"})

@app.route('/api/master/item', methods=['POST'])
def api_master_single():
    data = request.json
    key = data.get('key')
    item_data = data.get('data')
    
    master_file = 'master_data.json'
    with open(master_file, 'r') as f: db = json.load(f)
    
    if key in db['items']:
        db['items'][key]['base_price'] = item_data['base_price']
        db['items'][key]['default_discs'] = item_data['default_discs']
        db['items'][key]['is_netto'] = item_data['is_netto']
        db['items'][key]['is_taxable'] = item_data['is_taxable']
        
        if item_data.get('custom_rule'):
            db['items'][key]['custom_rule'] = item_data['custom_rule']
        else:
            if 'custom_rule' in db['items'][key]:
                del db['items'][key]['custom_rule']
                
    with open(master_file, 'w') as f: json.dump(db, f, indent=4)
    return jsonify({"status": "ok"})

@app.route('/api/delays', methods=['GET', 'POST'])
def api_delays():
    coord1_file = 'coordinates.json'
    coord2_file = 'coordinates_phase2.json'
    
    if request.method == 'POST':
        data = request.json
        step_id = data.get('step_id')
        val = data.get('custom_delay')
        phase = data.get('phase')
        
        target_file = coord1_file if phase == 'phase1' else coord2_file
        
        if os.path.exists(target_file):
            with open(target_file, 'r') as f: coords = json.load(f)
            if step_id in coords:
                if val is None or str(val).strip() == "":
                    if 'custom_delay' in coords[step_id]:
                        del coords[step_id]['custom_delay']
                else:
                    coords[step_id]['custom_delay'] = float(val)
                    
            with open(target_file, 'w') as f: json.dump(coords, f, indent=4)
        return jsonify({"status": "ok"})
        
    # GET Request: Kirim kedua file koordinat
    coords1 = {}
    coords2 = {}
    if os.path.exists(coord1_file):
        with open(coord1_file, 'r') as f: coords1 = json.load(f)
    if os.path.exists(coord2_file):
        with open(coord2_file, 'r') as f: coords2 = json.load(f)
        
    return jsonify({"phase1": coords1, "phase2": coords2})

class ServerThread(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.server = make_server('127.0.0.1', 5000, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()

server_instance = None

def start_server():
    global server_instance
    if server_instance is None:
        server_instance = ServerThread(app)
        server_instance.start()

def stop_server():
    global server_instance
    if server_instance:
        server_instance.shutdown()
        server_instance = None