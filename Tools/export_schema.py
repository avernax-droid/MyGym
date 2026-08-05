# Roda: python export_schema.py > schema.txt

import mysql.connector

DB_CONFIG ={
    'host': '127.0.0.1',
    'user': 'root',
    'port': 3307,
    'password': 'TonMix#25',
    'database': 'mygym'  # <- troca aqui
}


def get_column_type(row):
    return row['COLUMN_TYPE']

def get_key(row):
    keys = []
    if row['COLUMN_KEY'] == 'PRI':
        keys.append('PK')
    if row['EXTRA'] == 'auto_increment':
        keys.append('AI')
    if row['COLUMN_KEY'] == 'MUL':
        keys.append('FK') 
    return ','.join(keys) if keys else '-'

def main():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT 
        TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, COLUMN_KEY, EXTRA, ORDINAL_POSITION
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = %s
    ORDER BY TABLE_NAME, ORDINAL_POSITION;
    """
    cursor.execute(query, (DB_CONFIG['database'],))
    rows = cursor.fetchall()

    # Cabeçalho igual ao seu exemplo
    print(f"{'TABELA':<25} {'COLUNA':<25} {'TIPO':<60} {'CHAVE':<10} {'ORD_TABELA':<20} {'ORD_COLUNA':<12} {'ORDEM_TIPO'}")
    
    last_table = None
    for row in rows:
        table_name = row['TABLE_NAME']
        
        if last_table and last_table != table_name:
            print(f"{'----------':<25} {'----------':<25} {'----------':<60} {'----------':<10} {last_table:<20} {999:<12} {1}")
        
        tabela_col = table_name if last_table != table_name else ''
        print(f"{tabela_col:<25} {row['COLUMN_NAME']:<25} {get_column_type(row):<60} {get_key(row):<10} {table_name:<20} {row['ORDINAL_POSITION']:<12} {0}")
        last_table = table_name

    if last_table:
        print(f"{'----------':<25} {'----------':<25} {'----------':<60} {'----------':<10} {last_table:<20} {999:<12} {1}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()