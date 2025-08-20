#!/usr/bin/env python3
"""
Dashboard de métricas MCP basado en archivo - Lee métricas en tiempo real
"""
import json
import time
import os
from datetime import datetime
from pathlib import Path

def clear_screen():
    """Limpiar pantalla"""
    os.system('clear' if os.name == 'posix' else 'cls')

def read_metrics_file():
    """Leer métricas del archivo JSON"""
    metrics_file = Path("mcp_metrics_live.json")
    
    if not metrics_file.exists():
        return None
    
    try:
        with open(metrics_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error leyendo archivo de métricas: {e}")
        return None

def show_live_dashboard():
    """Mostrar dashboard en tiempo real basado en archivo"""
    print("DASHBOARD DE MÉTRICAS MCP - ARCHIVO EN TIEMPO REAL")
    print("=" * 70)
    print("Basado en archivo: mcp_metrics_live.json")
    print("Actualizando cada 3 segundos... (Ctrl+C para salir)")
    print()
    
    try:
        while True:
            clear_screen()
            print("DASHBOARD DE MÉTRICAS MCP - ARCHIVO EN TIEMPO REAL")
            print("=" * 70)
            print(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")
            print("-" * 70)
            
            data = read_metrics_file()
            
            if not data:
                print("Archivo de métricas no encontrado")
                print("Ejecuta consultas en ADK Web para generar métricas")
                print("Las métricas se guardan en: mcp_metrics_live.json")
            else:
                summary = data.get("summary", {})
                metrics = data.get("metrics", [])
                
                print(f"Total de consultas: {summary.get('total_queries', 0)}")
                print(f"Errores: {summary.get('error_count', 0)}")
                print(f"Métricas en archivo: {len(metrics)}")
                
                if metrics:
                    avg_latency = summary.get('avg_latency', 0)
                    print(f"Latencia promedio: {avg_latency:.1f}ms")
                    
                    # Análisis de tipos de fallback
                    fallback_counts = {}
                    for metric in metrics:
                        fb = metric.get('fallback_used', 'unknown')
                        fallback_counts[fb] = fallback_counts.get(fb, 0) + 1
                    
                    print("\nTIPOS DE FALLBACK:")
                    for fb_type, count in fallback_counts.items():
                        percentage = (count / len(metrics)) * 100
                        print(f"   {fb_type}: {count} ({percentage:.1f}%)")
                    
                    print("\nÚLTIMAS CONSULTAS:")
                    recent_metrics = metrics[-5:]  # Últimas 5
                    for i, metric in enumerate(recent_metrics, 1):
                        status = "ERROR" if metric.get('error') else "OK"
                        query = metric.get('query', 'N/A')[:40]
                        latency = metric.get('latency_ms', 0)
                        fallback = metric.get('fallback_used', 'unknown')
                        timestamp = metric.get('timestamp', '')[:19]  # Solo fecha y hora
                        print(f"   {i}. [{status}] '{query}...' | {latency}ms | {fallback} | {timestamp}")
                    
                    last_updated = summary.get('last_updated', 'N/A')
                    print(f"\nÚltimo registro: {last_updated[:19] if last_updated != 'N/A' else 'N/A'}")
                else:
                    print("\nSin métricas en archivo aún")
                    print("Ejecuta consultas en ADK Web para ver métricas")
            
            print("\n" + "=" * 70)
            print("Actualizando cada 3 segundos... (Ctrl+C para salir)")
            
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\n\nDashboard cerrado por usuario")

if __name__ == "__main__":
    show_live_dashboard()
