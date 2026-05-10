# services/acessos.py - Funções de backend para SIG Gestão
import hashlib
import sqlite3
from datetime import datetime
import pandas as pd

DB_FILE = 'sig_gestao.db'
ALLOWED_TABLES = {
    'users', 'pessoas', 'vendas', 'audits',
    'system_modules', 'buildings', 'equipamentos', 'equipamento_ambiente',
    'monitoramento', 'heatmap_data'
}


def get_db_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)


def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  role TEXT CHECK(role IN ('admin', 'user', 'guest')) NOT NULL)''')

    c.execute('''CREATE TABLE IF NOT EXISTS pessoas
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nome TEXT NOT NULL,
                  cpf TEXT UNIQUE NOT NULL,
                  tel TEXT NOT NULL,
                  cep TEXT NOT NULL,
                  data_nasc TEXT NOT NULL)''')

    c.execute('''CREATE TABLE IF NOT EXISTS vendas
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  pessoa_id INTEGER,
                  valor REAL NOT NULL,
                  data TEXT NOT NULL,
                  produto TEXT NOT NULL,
                  FOREIGN KEY(pessoa_id) REFERENCES pessoas(id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS audits
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  action TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS system_modules
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nome TEXT UNIQUE NOT NULL,
                  descricao TEXT,
                  criado_em TEXT NOT NULL)''')

    c.execute('''CREATE TABLE IF NOT EXISTS buildings
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nome TEXT UNIQUE NOT NULL,
                  localizacao TEXT NOT NULL,
                  capacidade INTEGER NOT NULL,
                  status TEXT NOT NULL DEFAULT 'Ativo')''')

    c.execute('''CREATE TABLE IF NOT EXISTS equipamentos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nome TEXT NOT NULL,
                  tipo TEXT NOT NULL,
                  serial TEXT UNIQUE NOT NULL,
                  status TEXT NOT NULL DEFAULT 'Operando')''')

    c.execute('''CREATE TABLE IF NOT EXISTS equipamento_ambiente
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  equipamento_id INTEGER NOT NULL,
                  ambiente_id INTEGER NOT NULL,
                  alocacao_data TEXT NOT NULL,
                  FOREIGN KEY(equipamento_id) REFERENCES equipamentos(id),
                  FOREIGN KEY(ambiente_id) REFERENCES buildings(id),
                  UNIQUE(equipamento_id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS monitoramento
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ambiente_id INTEGER NOT NULL,
                  area TEXT NOT NULL,
                  status TEXT NOT NULL,
                  temperatura REAL NOT NULL,
                  ocupacao INTEGER NOT NULL,
                  atualizado_em TEXT NOT NULL,
                  FOREIGN KEY(ambiente_id) REFERENCES buildings(id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS heatmap_data
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ambiente_id INTEGER NOT NULL,
                  intensidade REAL NOT NULL,
                  tipo TEXT NOT NULL,
                  registrado_em TEXT NOT NULL,
                  FOREIGN KEY(ambiente_id) REFERENCES buildings(id))''')

    conn.commit()
    conn.close()


def load_df(nome_tabela):
    if nome_tabela not in ALLOWED_TABLES:
        raise ValueError(f"Tabela inválida: {nome_tabela}")
    conn = get_db_connection()
    df = pd.read_sql_query(f"SELECT * FROM {nome_tabela}", conn)
    conn.close()
    return df


def generate_fake_data():
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        users = [
            ('admin', hashlib.sha256('admin123'.encode()).hexdigest(), 'admin'),
            ('user', hashlib.sha256('user123'.encode()).hexdigest(), 'user'),
            ('guest', hashlib.sha256('guest123'.encode()).hexdigest(), 'guest'),
        ]
        c.executemany("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", users)

    c.execute("SELECT COUNT(*) FROM pessoas")
    if c.fetchone()[0] == 0:
        pessoas = [
            ('João Silva', '123.456.789-00', '(61) 99999-0000', '70000-000', '01/01/1990'),
            ('Maria Souza', '987.654.321-00', '(61) 98888-1111', '70000-010', '15/05/1985'),
        ]
        c.executemany("INSERT INTO pessoas (nome, cpf, tel, cep, data_nasc) VALUES (?, ?, ?, ?, ?)", pessoas)

    c.execute("SELECT COUNT(*) FROM vendas")
    if c.fetchone()[0] == 0:
        c.execute("SELECT id FROM pessoas LIMIT 1")
        row = c.fetchone()
        pessoa_id = row[0] if row is not None else 1
        vendas = [
            (pessoa_id, 250.0, '2025-01-01', 'Serviço A'),
            (pessoa_id, 450.0, '2025-02-15', 'Serviço B'),
        ]
        c.executemany("INSERT INTO vendas (pessoa_id, valor, data, produto) VALUES (?, ?, ?, ?)", vendas)

    c.execute("SELECT COUNT(*) FROM system_modules")
    if c.fetchone()[0] == 0:
        modules = [
            ('Controle de Acesso', 'Gerencia perfis e acessos ao sistema', datetime.now().strftime('%Y-%m-%d')),
            ('Gerenciamento de Equipamentos', 'Administra equipamentos e alocações', datetime.now().strftime('%Y-%m-%d')),
            ('Monitoramento de Ambientes', 'Monitoramento em tempo real de prédios e estacionamento', datetime.now().strftime('%Y-%m-%d')),
        ]
        c.executemany("INSERT INTO system_modules (nome, descricao, criado_em) VALUES (?, ?, ?)", modules)

    c.execute("SELECT COUNT(*) FROM buildings")
    if c.fetchone()[0] == 0:
        buildings = [
            ('Prédio Alpha', 'Setor Central', 400, 'Ativo'),
            ('Prédio Beta', 'Setor Industrial', 250, 'Ativo'),
        ]
        c.executemany("INSERT INTO buildings (nome, localizacao, capacidade, status) VALUES (?, ?, ?, ?)", buildings)

    c.execute("SELECT COUNT(*) FROM equipamentos")
    if c.fetchone()[0] == 0:
        equipamentos = [
            ('Câmera Perimetral', 'Vídeo', 'SN-0001', 'Operando'),
            ('Sensor de Presença', 'Sensor', 'SN-0002', 'Operando'),
        ]
        c.executemany("INSERT INTO equipamentos (nome, tipo, serial, status) VALUES (?, ?, ?, ?)", equipamentos)

    c.execute("SELECT COUNT(*) FROM equipamento_ambiente")
    if c.fetchone()[0] == 0:
        c.execute("SELECT id FROM equipamentos LIMIT 1")
        eq_id = c.fetchone()[0]
        c.execute("SELECT id FROM buildings LIMIT 1")
        ambiente_id = c.fetchone()[0]
        c.execute("INSERT INTO equipamento_ambiente (equipamento_id, ambiente_id, alocacao_data) VALUES (?, ?, ?)",
                  (eq_id, ambiente_id, datetime.now().strftime('%Y-%m-%d')))

    c.execute("SELECT COUNT(*) FROM monitoramento")
    if c.fetchone()[0] == 0:
        c.execute("SELECT id FROM buildings LIMIT 1")
        ambiente_id = c.fetchone()[0]
        monitor = [
            (ambiente_id, 'Salas de Controle', 'Online', 22.5, 36, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            (ambiente_id, 'Entrada Principal', 'Online', 18.9, 12, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        ]
        c.executemany("INSERT INTO monitoramento (ambiente_id, area, status, temperatura, ocupacao, atualizado_em) VALUES (?, ?, ?, ?, ?, ?)", monitor)

    c.execute("SELECT COUNT(*) FROM heatmap_data")
    if c.fetchone()[0] == 0:
        c.execute("SELECT id FROM buildings LIMIT 1")
        ambiente_id = c.fetchone()[0]
        heatmap = [
            (ambiente_id, 0.85, 'Ocorrências', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            (ambiente_id, 0.60, 'Fluxo', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        ]
        c.executemany("INSERT INTO heatmap_data (ambiente_id, intensidade, tipo, registrado_em) VALUES (?, ?, ?, ?)", heatmap)

    conn.commit()
    conn.close()


def authenticate(username, password):
    if not username or not password:
        return None, None
    conn = get_db_connection()
    c = conn.cursor()
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT id, role FROM users WHERE username = ? AND password = ?", (username, pwd_hash))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0], row[1]
    return None, None


def log_audit(user_id, action):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO audits (user_id, action, created_at) VALUES (?, ?, ?)",
              (user_id, action, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()


class Pessoa:
    def __init__(self, nome, cpf, tel, cep, data_nasc):
        nome = str(nome or '').strip()
        cpf = str(cpf or '').strip()
        tel = str(tel or '').strip()
        cep = str(cep or '').strip()
        data_nasc = str(data_nasc or '').strip()

        if not nome:
            raise ValueError('Nome obrigatório.')
        if len(cpf) < 11 or not cpf.replace('.', '').replace('-', '').isdigit():
            raise ValueError('CPF inválido.')
        if len(tel) < 8 or not any(ch.isdigit() for ch in tel):
            raise ValueError('Telefone inválido.')
        if len(cep) < 5 or not cep.replace('-', '').isdigit():
            raise ValueError('CEP inválido.')
        if len(data_nasc) < 8:
            raise ValueError('Data de nascimento inválida.')

        self.nome = nome
        self.cpf = cpf
        self.tel = tel
        self.cep = cep
        self.data_nasc = data_nasc
