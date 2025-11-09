"""
GOST Windows Service - запускается на Windows хосте
Принимает HTTP запросы и выполняет csptest.exe
"""
from flask import Flask, jsonify, request
import subprocess
from datetime import datetime
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CSPTEST_PATH = r"C:\Program Files\Crypto Pro\CSP\csptest.exe"
CERT_NAME = "VTB Test User"


@app.route('/test', methods=['POST'])
def test_gost():
    """Тест GOST TLS подключения"""
    import random
    request_id = random.randint(1000, 9999)
    logger.info(f"🔔 Получен запрос на тест GOST... [ID: {request_id}]")
    start_time = datetime.now()
    
    try:
        cmd = [
            CSPTEST_PATH,
            "-tlsc",
            "-server", "api.gost.bankingapi.ru",
            "-port", "8443",
            "-exchange", "3",
            "-user", CERT_NAME,
            "-proto", "6",
            "-verbose"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='cp866',
            errors='replace',
            timeout=30
        )
        
        output = result.stdout + result.stderr
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # Success определяется по handshake
        success = "Handshake was successful" in output
        
        # Извлечь cipher
        cipher = None
        for line in output.split('\n'):
            if "TLS_GOSTR" in line and "CipherSuite" in line:
                if "TLS_GOSTR341112_256_WITH_KUZNYECHIK" in line:
                    cipher = "TLS_GOSTR341112_256_WITH_KUZNYECHIK_CTR_OMAC"
                break
        
        # Извлечь сервер
        server = None
        if "Банк ВТБ" in output:
            server = "Банк ВТБ (ПАО)"
        
        logger.info(f"✅ GOST тест завершен [ID: {request_id}]: success={success}, time={elapsed:.2f}s")
        
        # Извлечь ключевые строки для доказательства
        proof_lines = []
        for line in output.split('\n'):
            if any(keyword in line for keyword in ['Handshake', 'CipherSuite', 'Protocol', 'Subject:', 'ОГРН', 'ИНН']):
                proof_lines.append(line.strip())
        
        return jsonify({
            "success": success,
            "cipher": cipher or "GOST",
            "server": server or "api.gost.bankingapi.ru",
            "time": elapsed,
            "request_id": request_id,  # УНИКАЛЬНЫЙ ID ЗАПРОСА!
            "message": "GOST TLS handshake successful" if success else "GOST TLS handshake failed",
            "proof": proof_lines[:10] if success else None,  # Первые 10 строк доказательства
            "output": output if not success else None  # Полный вывод только при ошибке
        })
        
    except subprocess.TimeoutExpired:
        logger.error("❌ Timeout при выполнении csptest")
        return jsonify({
            "success": False,
            "error": "Timeout",
            "message": "GOST connection timeout"
        }), 500
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": f"GOST test failed: {str(e)}"
        }), 500


@app.route('/status', methods=['GET'])
def get_status():
    """Статус сервиса"""
    import os
    csptest_exists = os.path.exists(CSPTEST_PATH)
    
    return jsonify({
        "service": "GOST Windows Service",
        "status": "running",
        "csptest_available": csptest_exists,
        "csptest_path": CSPTEST_PATH,
        "cert_name": CERT_NAME
    })


if __name__ == '__main__':
    print("🚀 Starting GOST Windows Service...")
    print(f"   CSPTEST: {CSPTEST_PATH}")
    print(f"   CERT: {CERT_NAME}")
    print(f"   Listening on http://localhost:5555")
    
    app.run(host='0.0.0.0', port=5555, debug=False)

