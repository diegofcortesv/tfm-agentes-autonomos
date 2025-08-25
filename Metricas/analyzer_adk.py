import json
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Any
import re
from collections import Counter

class ADKSessionAnalyzer:
    def __init__(self):
        self.sessions_data = []
        self.metrics_summary = {}
        
        # ACTUALIZADO: Palabras clave consistentes con SentimentAnalyzer real
        self.urgency_keywords = [
            "urgente", "inmediato", "rápido", "ya", "ahora", "crisis",
            "crítico", "critico", "emergencia", "prioritario", "cuanto antes",
            "no puede esperar", "necesito ya", "¡urgente!", "urgencia",
            "emergente", "inmediatamente", "ahora mismo"
        ]
        
        self.negative_keywords = [
            "molesto", "enojado", "frustrado", "terrible", "horrible", 
            "malo", "lento", "problema", "error", "falla", "deficiente",
            "pésimo", "inaceptable", "indignado", "furioso", "decepcionado"
        ]
        
        self.escalation_keywords = [
            "supervisor", "gerente", "queja", "demanda", "legal",
            "cancelar", "cerrar cuenta", "competencia", "abogado",
            "formal complaint", "escalate", "manager"
        ]
        
        # NUEVO: Patrones de estado del sistema (servidor caído, etc.)
        self.system_status_keywords = [
            "caído", "caido", "no responde", "no funciona", "fuera de servicio",
            "down", "corrupta", "fallo", "timeout", "error crítico"
        ]
    
    def load_session(self, filepath: str, session_name: str = None) -> Dict:
        """Carga un archivo JSON de sesión ADK"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            session_info = {
                'filepath': filepath,
                'session_name': session_name or filepath.split('/')[-1],
                'data': session_data,
                'analysis': {}
            }
            
            self.sessions_data.append(session_info)
            return session_info
            
        except Exception as e:
            print(f"Error cargando {filepath}: {e}")
            return None
    
    def extract_user_queries(self, session_data: Dict) -> pd.DataFrame:
        """Extrae todas las consultas de usuario de una sesión"""
        user_queries = []
        
        for event in session_data.get('events', []):
            if event.get('content', {}).get('role') == 'user':
                for part in event.get('content', {}).get('parts', []):
                    if 'text' in part:
                        user_queries.append({
                            'session_id': session_data.get('id'),
                            'event_id': event.get('id'),
                            'timestamp': event.get('timestamp'),
                            'query': part['text'],
                            'author': event.get('author', 'user'),
                            'invocation_id': event.get('invocationId')
                        })
        
        df = pd.DataFrame(user_queries)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df = df.sort_values('timestamp').reset_index(drop=True)
        
        return df
    
    def calculate_response_times_corrected(self, session_data: Dict) -> Dict:
        """Calcula tiempos de respuesta de manera corregida"""
        events = session_data.get('events', [])
        
        # Ordenar eventos por timestamp
        sorted_events = sorted(events, key=lambda x: x.get('timestamp', 0))
        
        response_times = []
        query_response_pairs = []
        
        i = 0
        while i < len(sorted_events):
            current_event = sorted_events[i]
            
            # Es una consulta de usuario?
            if (current_event.get('content', {}).get('role') == 'user' and 
                current_event.get('author') == 'user'):
                
                user_timestamp = current_event.get('timestamp')
                invocation_id = current_event.get('invocationId')
                
                # Buscar la respuesta final correspondiente
                j = i + 1
                while j < len(sorted_events):
                    next_event = sorted_events[j]
                    
                    # Respuesta del ResponseSynthesizer o respuesta final
                    if (next_event.get('author') == 'ResponseSynthesizer' or
                        'synthesized_response' in next_event.get('actions', {}).get('stateDelta', {})):
                        
                        response_timestamp = next_event.get('timestamp')
                        
                        if response_timestamp and user_timestamp and response_timestamp > user_timestamp:
                            response_time = response_timestamp - user_timestamp
                            response_times.append(response_time)
                            
                            query_response_pairs.append({
                                'user_query': current_event.get('content', {}).get('parts', [{}])[0].get('text', ''),
                                'user_timestamp': user_timestamp,
                                'response_timestamp': response_timestamp,
                                'response_time': response_time,
                                'invocation_id': invocation_id
                            })
                            break
                    j += 1
            i += 1
        
        return {
            'response_times': response_times,
            'query_response_pairs': query_response_pairs,
            'avg_response_time': np.mean(response_times) if response_times else 0,
            'min_response_time': min(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0,
            'valid_pairs_count': len(query_response_pairs)
        }
    
    def analyze_rag_effectiveness_detailed(self, session_data: Dict) -> Dict:
        """Análisis detallado de efectividad RAG"""
        events = session_data.get('events', [])
        
        rag_operations = []
        
        for i, event in enumerate(events):
            content = event.get('content', {})
            
            # Buscar function calls de búsqueda
            for part in content.get('parts', []):
                if 'functionCall' in part:
                    func_call = part['functionCall']
                    if func_call.get('name') == 'search_knowledge':
                        
                        # Buscar la respuesta correspondiente
                        response_found = False
                        response_quality = 'no_response'
                        response_content = ''
                        
                        # Buscar en eventos posteriores la respuesta
                        for j in range(i + 1, min(i + 10, len(events))):
                            next_event = events[j]
                            next_content = next_event.get('content', {})
                            
                            for next_part in next_content.get('parts', []):
                                if 'functionResponse' in next_part:
                                    func_response = next_part['functionResponse']
                                    if (func_response.get('name') == 'search_knowledge' and
                                        func_response.get('id') == func_call.get('id')):
                                        
                                        response_found = True
                                        response_content = str(func_response.get('response', ''))
                                        
                                        # Evaluar calidad de respuesta
                                        if not response_content or response_content.strip() == '':
                                            response_quality = 'empty'
                                        elif 'no encontr' in response_content.lower() or 'no results' in response_content.lower():
                                            response_quality = 'no_results'
                                        elif len(response_content) > 100:  # Respuesta sustantiva
                                            response_quality = 'good'
                                        else:
                                            response_quality = 'minimal'
                                        break
                            
                            if response_found:
                                break
                        
                        rag_operations.append({
                            'query': func_call.get('args', {}).get('query', ''),
                            'timestamp': event.get('timestamp'),
                            'event_id': event.get('id'),
                            'function_call_id': func_call.get('id'),
                            'response_found': response_found,
                            'response_quality': response_quality,
                            'response_length': len(response_content),
                            'invocation_id': event.get('invocationId')
                        })
        
        # Calcular métricas
        total_rag_queries = len(rag_operations)
        successful_queries = len([op for op in rag_operations if op['response_quality'] in ['good', 'minimal']])
        good_quality_queries = len([op for op in rag_operations if op['response_quality'] == 'good'])
        
        return {
            'total_rag_queries': total_rag_queries,
            'successful_queries': successful_queries,
            'good_quality_queries': good_quality_queries,
            'success_rate_percentage': (successful_queries / total_rag_queries * 100) if total_rag_queries > 0 else 0,
            'good_quality_rate_percentage': (good_quality_queries / total_rag_queries * 100) if total_rag_queries > 0 else 0,
            'rag_operations_detail': rag_operations,
            'response_quality_distribution': Counter([op['response_quality'] for op in rag_operations])
        }
    
    def analyze_urgency_consistent_with_sentiment_analyzer(self, session_data: Dict) -> Dict:
        """
        MEJORADO: Análisis de urgencia consistente con el SentimentAnalyzer real
        Basado en los criterios encontrados en el project knowledge
        """
        user_queries = self.extract_user_queries(session_data)
        
        urgency_cases = []
        
        for idx, query_row in user_queries.iterrows():
            text = query_row['query'].lower()
            urgency_score = 0
            detected_patterns = []
            
            # 1. DETECCIÓN DE PALABRAS CLAVE DE URGENCIA (consistente con SentimentAnalyzer)
            urgency_keyword_count = 0
            for keyword in self.urgency_keywords:
                if keyword.lower() in text:
                    detected_patterns.append({'category': 'urgency', 'keyword': keyword})
                    urgency_keyword_count += 1
            
            # 2. DETECCIÓN DE PALABRAS DE ESTADO CRÍTICO DEL SISTEMA
            system_critical_count = 0
            for keyword in self.system_status_keywords:
                if keyword.lower() in text:
                    detected_patterns.append({'category': 'system_critical', 'keyword': keyword})
                    system_critical_count += 1
            
            # 3. DETECCIÓN DE PALABRAS NEGATIVAS (indicador de frustración)
            negative_keyword_count = 0
            for keyword in self.negative_keywords:
                if keyword.lower() in text:
                    detected_patterns.append({'category': 'negative', 'keyword': keyword})
                    negative_keyword_count += 1
            
            # 4. DETECCIÓN DE ESCALACIÓN
            escalation_keyword_count = 0
            for keyword in self.escalation_keywords:
                if keyword.lower() in text:
                    detected_patterns.append({'category': 'escalation', 'keyword': keyword})
                    escalation_keyword_count += 1
            
            # CÁLCULO DEL SCORE SEGÚN LA LÓGICA DEL SENTIMENTANALYZER REAL
            # Basado en los pesos observados en los JSONs del project knowledge
            
            # Palabras de urgencia: peso alto
            urgency_score += urgency_keyword_count * 2
            
            # Problemas críticos del sistema: peso muy alto
            urgency_score += system_critical_count * 3
            
            # Palabras negativas: peso moderado
            urgency_score += min(negative_keyword_count, 2)  # Máximo 2 puntos
            
            # Escalación: peso alto
            urgency_score += escalation_keyword_count * 2
            
            # Detectar signos de exclamación como intensificadores
            exclamation_count = text.count('!')
            urgency_score += min(exclamation_count, 2)
            
            # Detectar palabras en mayúsculas (EMERGENCIA, YA, etc.)
            uppercase_words = len([word for word in text.split() if word.isupper() and len(word) > 2])
            urgency_score += min(uppercase_words, 2)
            
            # Detectar frases temporales críticas (hace X minutos/horas)
            time_pattern = r'hace\s+\d+\s+(minuto|hora|día)'
            if re.search(time_pattern, text):
                detected_patterns.append({'category': 'time_critical', 'keyword': 'tiempo_específico'})
                urgency_score += 2
            
            # CLASIFICACIÓN FINAL (consistente con detected_keywords del SentimentAnalyzer)
            urgency_level = 'normal'
            if urgency_score >= 4 or system_critical_count > 0:  # Criterio más estricto
                urgency_level = 'high'
            elif urgency_score >= 2:
                urgency_level = 'medium'
            
            # Determinar escalation_risk
            escalation_risk = 'low'
            if escalation_keyword_count > 0 or negative_keyword_count >= 2:
                escalation_risk = 'high'
            elif urgency_score >= 4:
                escalation_risk = 'medium'
            
            # Simular el formato de respuesta del SentimentAnalyzer real
            sentiment_analyzer_format = {
                'detected_keywords': {
                    'positive': 0,  # No implementamos detección positiva en este contexto
                    'negative': negative_keyword_count,
                    'urgency': urgency_keyword_count,
                    'escalation': escalation_keyword_count
                },
                'urgency_level': urgency_level,
                'escalation_risk': escalation_risk
            }
            
            if urgency_score > 0 or detected_patterns:
                urgency_cases.append({
                    'query': query_row['query'],
                    'urgency_score': urgency_score,
                    'urgency_level': urgency_level,
                    'escalation_risk': escalation_risk,
                    'detected_patterns': detected_patterns,
                    'timestamp': query_row['timestamp'],
                    'event_id': query_row['event_id'],
                    'sentiment_analyzer_format': sentiment_analyzer_format  # NUEVO
                })
        
        return {
            'total_queries': len(user_queries),
            'urgency_cases': urgency_cases,
            'urgency_cases_count': len(urgency_cases),
            'urgency_percentage': (len(urgency_cases) / len(user_queries) * 100) if len(user_queries) > 0 else 0,
            'high_urgency_count': len([case for case in urgency_cases if case['urgency_level'] == 'high']),
            'medium_urgency_count': len([case for case in urgency_cases if case['urgency_level'] == 'medium']),
            'low_urgency_count': len([case for case in urgency_cases if case['urgency_level'] == 'normal']),
            'urgency_level_distribution': Counter([case['urgency_level'] for case in urgency_cases]),
            'escalation_risk_distribution': Counter([case['escalation_risk'] for case in urgency_cases])
        }
    
    def create_detailed_query_analysis(self) -> pd.DataFrame:
        """Crea un CSV detallado con análisis por consulta MEJORADO"""
        detailed_analysis = []
        
        for session_info in self.sessions_data:
            session_data = session_info['data']
            session_name = session_info['session_name']
            
            # Obtener análisis de la sesión (USANDO MÉTODO MEJORADO)
            user_queries = self.extract_user_queries(session_data)
            response_times_data = self.calculate_response_times_corrected(session_data)
            rag_analysis = self.analyze_rag_effectiveness_detailed(session_data)
            urgency_analysis = self.analyze_urgency_consistent_with_sentiment_analyzer(session_data)
            
            # Crear mapas para lookup rápido
            response_time_map = {pair['user_query']: pair['response_time'] for pair in response_times_data['query_response_pairs']}
            
            rag_map = {}
            for rag_op in rag_analysis['rag_operations_detail']:
                closest_query = None
                min_time_diff = float('inf')
                
                for idx, query_row in user_queries.iterrows():
                    time_diff = abs(rag_op['timestamp'] - query_row['timestamp'].timestamp())
                    if time_diff < min_time_diff:
                        min_time_diff = time_diff
                        closest_query = query_row['query']
                
                if closest_query and min_time_diff < 10:
                    if closest_query not in rag_map:
                        rag_map[closest_query] = []
                    rag_map[closest_query].append(rag_op)
            
            urgency_map = {case['query']: case for case in urgency_analysis['urgency_cases']}
            
            # Procesar cada consulta de usuario
            for idx, query_row in user_queries.iterrows():
                query_text = query_row['query']
                
                # Datos básicos
                row_data = {
                    'session_name': session_name,
                    'session_id': query_row['session_id'],
                    'query_number': idx + 1,
                    'query_text': query_text,
                    'query_length_chars': len(query_text),
                    'query_length_words': len(query_text.split()),
                    'timestamp': query_row['timestamp'],
                    'event_id': query_row['event_id'],
                    'invocation_id': query_row['invocation_id']
                }
                
                # Tiempo de respuesta
                response_time = response_time_map.get(query_text, None)
                row_data.update({
                    'response_time_seconds': response_time,
                    'has_response_time': response_time is not None,
                    'response_time_category': 'fast' if response_time and response_time < 2 else 'medium' if response_time and response_time < 5 else 'slow' if response_time else 'no_data'
                })
                
                # Análisis RAG
                rag_ops = rag_map.get(query_text, [])
                row_data.update({
                    'rag_queries_triggered': len(rag_ops),
                    'rag_success': any(op['response_quality'] in ['good', 'minimal'] for op in rag_ops),
                    'rag_quality': 'good' if any(op['response_quality'] == 'good' for op in rag_ops) else 'minimal' if any(op['response_quality'] == 'minimal' for op in rag_ops) else 'poor' if rag_ops else 'none',
                    'rag_response_total_length': sum(op['response_length'] for op in rag_ops)
                })
                
                # ANÁLISIS DE URGENCIA MEJORADO - Consistente con SentimentAnalyzer
                urgency_info = urgency_map.get(query_text, {})
                sentiment_format = urgency_info.get('sentiment_analyzer_format', {})
                
                row_data.update({
                    'is_urgent': query_text in urgency_map,
                    'urgency_score': urgency_info.get('urgency_score', 0),
                    'urgency_level': urgency_info.get('urgency_level', 'normal'),
                    'escalation_risk': urgency_info.get('escalation_risk', 'low'),
                    'urgency_patterns_detected': len(urgency_info.get('detected_patterns', [])),
                    'urgency_keywords': ', '.join([p['keyword'] for p in urgency_info.get('detected_patterns', []) if p['category'] == 'urgency']),
                    # NUEVO: Campos consistentes con SentimentAnalyzer
                    'sentiment_negative_keywords': sentiment_format.get('detected_keywords', {}).get('negative', 0),
                    'sentiment_urgency_keywords': sentiment_format.get('detected_keywords', {}).get('urgency', 0),
                    'sentiment_escalation_keywords': sentiment_format.get('detected_keywords', {}).get('escalation', 0),
                    'consistent_with_sentiment_analyzer': urgency_info.get('urgency_level', 'normal') != 'normal'
                })
                
                # Análisis de contexto
                customer_id_pattern = r'CUST_\d{3}'
                customer_ids = re.findall(customer_id_pattern, query_text)
                contextual_words = ['anterior', 'previamente', 'reporté', 'seguimiento', 'actualización', 'novedades']
                has_context_ref = any(word in query_text.lower() for word in contextual_words)
                
                row_data.update({
                    'has_customer_id': len(customer_ids) > 0,
                    'customer_ids': ', '.join(customer_ids),
                    'has_contextual_reference': has_context_ref,
                    'query_type': 'followup' if has_context_ref else 'initial_with_id' if customer_ids else 'initial_anonymous'
                })
                
                detailed_analysis.append(row_data)
        
        return pd.DataFrame(detailed_analysis)
    
    def export_detailed_analysis(self, output_prefix: str = 'adk_detailed_analysis_v2'):
        """Exporta análisis detallado por consulta con mejoras de consistencia"""
        detailed_df = self.create_detailed_query_analysis()
        
        # Exportar CSV detallado
        detailed_file = f'{output_prefix}_per_query.csv'
        detailed_df.to_csv(detailed_file, index=False, encoding='utf-8')
        print(f"Análisis detallado por consulta exportado: {detailed_file}")
        
        # Crear resumen estadístico MEJORADO
        summary_stats = {
            'total_queries': len(detailed_df),
            'sessions_analyzed': detailed_df['session_name'].nunique(),
            'avg_response_time': detailed_df[detailed_df['response_time_seconds'].notna()]['response_time_seconds'].mean(),
            'queries_with_response_time': detailed_df['has_response_time'].sum(),
            'rag_success_rate': (detailed_df['rag_success'].sum() / len(detailed_df) * 100),
            'urgency_rate': (detailed_df['is_urgent'].sum() / len(detailed_df) * 100),
            'high_urgency_rate': (detailed_df[detailed_df['urgency_level'] == 'high'].shape[0] / len(detailed_df) * 100),
            'escalation_risk_high_rate': (detailed_df[detailed_df['escalation_risk'] == 'high'].shape[0] / len(detailed_df) * 100),
            'queries_with_customer_id': detailed_df['has_customer_id'].sum(),
            'contextual_queries': detailed_df['has_contextual_reference'].sum(),
            # NUEVAS MÉTRICAS CONSISTENTES CON SENTIMENTANALYZER
            'avg_sentiment_negative_keywords': detailed_df['sentiment_negative_keywords'].mean(),
            'avg_sentiment_urgency_keywords': detailed_df['sentiment_urgency_keywords'].mean(),
            'queries_consistent_with_sentiment_analyzer': detailed_df['consistent_with_sentiment_analyzer'].sum()
        }
        
        # Exportar resumen
        summary_df = pd.DataFrame([summary_stats])
        summary_file = f'{output_prefix}_summary_stats.csv'
        summary_df.to_csv(summary_file, index=False, encoding='utf-8')
        print(f"Resumen estadístico exportado: {summary_file}")
        
        # NUEVO: Reporte de consistencia
        consistency_report = self.generate_consistency_report(detailed_df)
        consistency_file = f'{output_prefix}_consistency_report.txt'
        with open(consistency_file, 'w', encoding='utf-8') as f:
            f.write(consistency_report)
        print(f"Reporte de consistencia exportado: {consistency_file}")
        
        return detailed_df, summary_stats
    
    def generate_consistency_report(self, detailed_df: pd.DataFrame) -> str:
        """Genera un reporte de consistencia con SentimentAnalyzer"""
        report = []
        report.append("="*60)
        report.append("REPORTE DE CONSISTENCIA CON SENTIMENTANALYZER")
        report.append("="*60)
        report.append("")
        
        total_queries = len(detailed_df)
        urgent_queries = detailed_df[detailed_df['urgency_level'] == 'high']
        
        report.append(f"Total de consultas analizadas: {total_queries}")
        report.append(f"Consultas marcadas como 'high urgency': {len(urgent_queries)}")
        report.append(f"Porcentaje de urgencia alta: {len(urgent_queries)/total_queries*100:.1f}%")
        report.append("")
        
        report.append("DISTRIBUCIÓN POR NIVEL DE URGENCIA:")
        urgency_dist = detailed_df['urgency_level'].value_counts()
        for level, count in urgency_dist.items():
            report.append(f"  {level}: {count} ({count/total_queries*100:.1f}%)")
        report.append("")
        
        report.append("DISTRIBUCIÓN POR RIESGO DE ESCALACIÓN:")
        escalation_dist = detailed_df['escalation_risk'].value_counts()
        for risk, count in escalation_dist.items():
            report.append(f"  {risk}: {count} ({count/total_queries*100:.1f}%)")
        report.append("")
        
        report.append("EJEMPLOS DE CONSULTAS DE ALTA URGENCIA DETECTADAS:")
        high_urgency_examples = urgent_queries[['query_text', 'urgency_score', 'urgency_keywords']].head(5)
        for idx, row in high_urgency_examples.iterrows():
            report.append(f"  • \"{row['query_text'][:100]}...\"")
            report.append(f"    Score: {row['urgency_score']}, Keywords: {row['urgency_keywords']}")
        report.append("")
        
        return "\n".join(report)

# Función main actualizada
def main():
    """Función principal para análisis de sesiones ADK con consistencia mejorada"""
    analyzer = ADKSessionAnalyzer()
    
    # Lista de archivos de sesión
    session_files = [
        'session 01 eficiencia operativa-a92f0dbe-9c76-4364-86ab-a00423e05604.json',
        'session 02 contexto-679d54c7-81ab-482a-93e4-99a49da29b62.json',
        'session 03 escalamiento-e3040610-5096-489e-92ae-1835e80811da.json',
        'session 04 Calidad RAG-476b0c92-1d76-4e51-8478-a2e605df0a90.json',
        'session 05 P1 persistencia-506b635f-8394-4d57-b7bc-ae0a5f3e9a88.json',
        'session 05 P2 persistencia-91016382-6507-417d-8485-4f172aca7bba.json'
    ]
    
    # Cargar sesiones
    loaded_sessions = 0
    for file in session_files:
        if analyzer.load_session(file):
            loaded_sessions += 1
            print(f"Cargado: {file}")
    
    print(f"\nSesiones cargadas exitosamente: {loaded_sessions}")
    
    if loaded_sessions == 0:
        print("Error: No se pudo cargar ninguna sesión.")
        return None
    
    # Generar análisis detallado con consistencia mejorada
    print("\nGenerando análisis detallado por consulta (VERSIÓN MEJORADA)...")
    detailed_df, summary_stats = analyzer.export_detailed_analysis()
    
    # Mostrar resumen MEJORADO
    print("\n" + "="*60)
    print("RESUMEN EJECUTIVO DEL ANÁLISIS - VERSIÓN CONSISTENTE")
    print("="*60)
    print(f"Total consultas analizadas: {summary_stats['total_queries']}")
    print(f"Sesiones procesadas: {summary_stats['sessions_analyzed']}")
    print(f"Tiempo respuesta promedio: {summary_stats['avg_response_time']:.3f} segundos")
    print(f"Consultas con tiempo de respuesta: {summary_stats['queries_with_response_time']}")
    print(f"Tasa éxito RAG: {summary_stats['rag_success_rate']:.1f}%")
    print(f"Tasa detección urgencia: {summary_stats['urgency_rate']:.1f}%")
    print(f"Tasa urgencia ALTA: {summary_stats['high_urgency_rate']:.1f}%")
    print(f"Tasa riesgo escalación ALTO: {summary_stats['escalation_risk_high_rate']:.1f}%")
    print(f"Consultas con ID cliente: {summary_stats['queries_with_customer_id']}")
    print(f"Consultas contextuales: {summary_stats['contextual_queries']}")
    print(f"Promedio keywords negativas: {summary_stats['avg_sentiment_negative_keywords']:.1f}")
    print(f"Promedio keywords urgencia: {summary_stats['avg_sentiment_urgency_keywords']:.1f}")
    print(f"Consultas consistentes con SentimentAnalyzer: {summary_stats['queries_consistent_with_sentiment_analyzer']}")
    
    # Análisis de validación cruzada
    print("\n" + "="*60)
    print("VALIDACIÓN CRUZADA CON SENTIMENTANALYZER")
    print("="*60)
    
    # Casos específicos de alta urgencia detectados
    high_urgency_cases = detailed_df[detailed_df['urgency_level'] == 'high']
    print(f"\nCasos de ALTA URGENCIA detectados: {len(high_urgency_cases)}")
    
    if len(high_urgency_cases) > 0:
        print("\nEjemplos de consultas de alta urgencia:")
        for idx, case in high_urgency_cases.head(3).iterrows():
            print(f"  • \"{case['query_text'][:80]}...\"")
            print(f"    Score: {case['urgency_score']}, Keywords urgencia: {case['sentiment_urgency_keywords']}")
            print(f"    Riesgo escalación: {case['escalation_risk']}")
            print()
    
    return analyzer, detailed_df

if __name__ == "__main__":
    analyzer, detailed_df = main()