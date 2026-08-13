# core/web_server.py
import json
import os
import threading
from flask import Flask, render_template_string, request, jsonify
from werkzeug.serving import make_server

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ERP Bot Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <nav class="navbar navbar-dark bg-dark mb-4">
        <div class="container-fluid">
            <span class="navbar-brand mb-0 h1">🤖 ERP Automation Dashboard</span>
        </div>
    </nav>
    <div class="container">
        <ul class="nav nav-tabs" id="myTab" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#stores">🏪 Store Manager</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" data-bs-toggle="tab" data-bs-target="#master">📦 Master Data</button>
            </li>
        </ul>
        <div class="tab-content bg-white p-4 border border-top-0 rounded-bottom" id="myTabContent">
            
            <!-- STORE MANAGER -->
            <div class="tab-pane fade show active" id="stores">
                <h4>Daftar Toko (Batch Mode)</h4>
                <div class="input-group mb-3">
                    <input type="text" id="newStoreName" class="form-control" placeholder="Nama Toko Baru">
                    <button class="btn btn-primary" onclick="addStore()">Tambah</button>
                </div>
                <ul class="list-group" id="storeList"></ul>
            </div>

            <!-- MASTER DATA -->
            <div class="tab-pane fade" id="master">
                <div class="d-flex justify-content-between mb-3">
                    <h4>Master Data Barang</h4>
                    <button class="btn btn-warning" onclick="openBatchModal()">✏️ Batch Update</button>
                </div>
                <input type="text" id="searchItem" class="form-control mb-3" placeholder="Cari barang..." onkeyup="filterTable()">
                <div class="table-responsive" style="max-height: 500px;">
                    <table class="table table-hover table-bordered" id="masterTable">
                        <thead class="table-dark sticky-top">
                            <tr>
                                <th><input type="checkbox" id="checkAll" onclick="toggleAll(this)"></th>
                                <th>Nama Barang</th>
                                <th>Harga Dasar</th>
                                <th>Diskon</th>
                                <th>Netto?</th>
                            </tr>
                        </thead>
                        <tbody id="masterBody"></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <!-- BATCH UPDATE MODAL -->
    <div class="modal fade" id="batchModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Batch Update (<span id="selectedCount">0</span> item)</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <label>Harga Baru (Kosongkan jika tidak diubah)</label>
                        <input type="number" id="batchPrice" class="form-control">
                    </div>
                    <div class="mb-3">
                        <label>Diskon Baru (Format: 45,10,0,0 - Kosongkan jika tidak diubah)</label>
                        <input type="text" id="batchDisc" class="form-control" placeholder="Contoh: 45,10,0,0">
                    </div>
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="batchNetto">
                        <label class="form-check-label">Set sebagai Netto</label>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Batal</button>
                    <button type="button" class="btn btn-primary" onclick="applyBatchUpdate()">Simpan Perubahan</button>
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
                    <button class="btn btn-sm btn-danger" onclick="deleteStore('${s.name}')">Hapus</button>
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
        }

        function renderMasterTable() {
            let html = '';
            for(let key in masterData.items) {
                let item = masterData.items[key];
                html += `<tr>
                    <td><input type="checkbox" class="item-check" value="${key}"></td>
                    <td class="item-name">${key}</td>
                    <td>Rp ${item.base_price}</td>
                    <td>${item.default_discs.join(' + ')}%</td>
                    <td>${item.is_netto ? '✅ Ya' : '❌ Tidak'}</td>
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

        function openBatchModal() {
            let selected = document.querySelectorAll('.item-check:checked');
            if(selected.length === 0) { alert("Pilih minimal 1 barang!"); return; }
            document.getElementById('selectedCount').innerText = selected.length;
            new bootstrap.Modal(document.getElementById('batchModal')).show();
        }

        async function applyBatchUpdate() {
            let selected = Array.from(document.querySelectorAll('.item-check:checked')).map(cb => cb.value);
            let price = document.getElementById('batchPrice').value;
            let disc = document.getElementById('batchDisc').value;
            let is_netto = document.getElementById('batchNetto').checked;

            let payload = { keys: selected, is_netto: is_netto };
            if(price) payload.base_price = parseFloat(price);
            if(disc) payload.default_discs = disc.split(',').map(Number);

            await fetch('/api/master/batch', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            
            bootstrap.Modal.getInstance(document.getElementById('batchModal')).hide();
            loadMaster();
        }

        window.onload = () => { loadStores(); loadMaster(); };
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
    master_file = 'master_data.json'
    with open(master_file, 'r') as f: db = json.load(f)
    
    for key in data['keys']:
        if key in db['items']:
            if 'base_price' in data: db['items'][key]['base_price'] = data['base_price']
            if 'default_discs' in data: db['items'][key]['default_discs'] = data['default_discs']
            db['items'][key]['is_netto'] = data['is_netto']
            
    with open(master_file, 'w') as f: json.dump(db, f, indent=4)
    return jsonify({"status": "ok"})

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