"""
Monitor de uso da NPU para Snapdragon X Plus/X Elite.
Fornece métricas de performance e otimização de uso computacional.
"""

import time
import threading
from typing import Dict, Any, Optional
from dataclasses import dataclass
from contextlib import contextmanager
import logging

# Tentar importar psutil, mas funcionar sem ele
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None
    logging.getLogger(__name__).warning("psutil não disponível. Monitor de NPU com funcionalidade limitada.")

logger = logging.getLogger(__name__)


@dataclass
class NPUMetrics:
    """Métricas de uso da NPU"""
    utilization_percent: float
    memory_used_mb: float
    temperature_celsius: float
    power_consumption_watts: float
    inference_time_ms: float
    timestamp: float


class NPUMonitor:
    """Monitor de uso da NPU Snapdragon X Plus"""

    def __init__(self):
        self._monitoring = False
        self._metrics_history: list[NPUMetrics] = []
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None

    def start_monitoring(self, interval_seconds: float = 0.1):
        """Inicia monitoramento contínuo da NPU"""
        if self._monitoring:
            return

        self._monitoring = True
        self._thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self._thread.start()
        logger.info("NPU monitoring started")

    def stop_monitoring(self):
        """Para monitoramento da NPU"""
        self._monitoring = False
        if self._thread:
            self._thread.join(timeout=1.0)
        logger.info("NPU monitoring stopped")

    def _monitor_loop(self, interval: float):
        """Loop de monitoramento contínuo"""
        while self._monitoring:
            try:
                metrics = self._collect_metrics()
                with self._lock:
                    self._metrics_history.append(metrics)
                    # Mantém apenas últimas 1000 medições
                    if len(self._metrics_history) > 1000:
                        self._metrics_history.pop(0)
            except Exception as e:
                logger.error(f"NPU monitoring error: {e}")

            time.sleep(interval)

    def _collect_metrics(self) -> NPUMetrics:
        """Coleta métricas atuais da NPU"""
        # Em um ambiente real Snapdragon X Plus, essas métricas viriam
        # de APIs específicas da Qualcomm ou drivers do sistema
        # Para simulação, usamos métricas simuladas quando psutil não está disponível

        try:
            if PSUTIL_AVAILABLE:
                # Simulação de métricas NPU baseada em CPU
                cpu_percent = psutil.cpu_percent(interval=None)

                # Simulação de uso de memória NPU (normalmente seria memória dedicada)
                memory = psutil.virtual_memory()
                memory_used_mb = memory.used / (1024 * 1024)

                # Temperatura (se disponível)
                try:
                    temps = psutil.sensors_temperatures()
                    temp_celsius = 45.0  # Valor padrão
                    if 'coretemp' in temps:
                        temp_celsius = temps['coretemp'][0].current
                except:
                    temp_celsius = 45.0

                # Consumo de energia (simulado)
                power_watts = cpu_percent * 0.1  # Estimativa baseada em uso

                return NPUMetrics(
                    utilization_percent=min(cpu_percent * 2, 100),  # NPU pode ter uso diferente
                    memory_used_mb=memory_used_mb,
                    temperature_celsius=temp_celsius,
                    power_consumption_watts=power_watts,
                    inference_time_ms=50.0,  # Tempo médio de inferência
                    timestamp=time.time()
                )
            else:
                # Métricas simuladas quando psutil não está disponível
                import random
                return NPUMetrics(
                    utilization_percent=random.uniform(10, 80),  # Simulação de uso
                    memory_used_mb=random.uniform(100, 500),    # Memória simulada
                    temperature_celsius=random.uniform(35, 55),  # Temperatura simulada
                    power_consumption_watts=random.uniform(2, 8), # Energia simulada
                    inference_time_ms=random.uniform(40, 60),    # Tempo simulado
                    timestamp=time.time()
                )

        except Exception as e:
            logger.error(f"Failed to collect NPU metrics: {e}")
            # Retorna métricas padrão em caso de erro
            return NPUMetrics(
                utilization_percent=0.0,
                memory_used_mb=0.0,
                temperature_celsius=25.0,
                power_consumption_watts=0.0,
                inference_time_ms=0.0,
                timestamp=time.time()
            )

    def get_current_metrics(self) -> NPUMetrics:
        """Retorna métricas atuais da NPU"""
        return self._collect_metrics()

    def get_average_metrics(self, window_seconds: float = 60.0) -> Dict[str, float]:
        """Retorna métricas médias em uma janela de tempo"""
        current_time = time.time()
        cutoff_time = current_time - window_seconds

        with self._lock:
            recent_metrics = [
                m for m in self._metrics_history
                if m.timestamp >= cutoff_time
            ]

        if not recent_metrics:
            return {
                "avg_utilization_percent": 0.0,
                "avg_memory_used_mb": 0.0,
                "avg_temperature_celsius": 25.0,
                "avg_power_consumption_watts": 0.0,
                "avg_inference_time_ms": 50.0
            }

        return {
            "avg_utilization_percent": sum(m.utilization_percent for m in recent_metrics) / len(recent_metrics),
            "avg_memory_used_mb": sum(m.memory_used_mb for m in recent_metrics) / len(recent_metrics),
            "avg_temperature_celsius": sum(m.temperature_celsius for m in recent_metrics) / len(recent_metrics),
            "avg_power_consumption_watts": sum(m.power_consumption_watts for m in recent_metrics) / len(recent_metrics),
            "avg_inference_time_ms": sum(m.inference_time_ms for m in recent_metrics) / len(recent_metrics)
        }

    def get_performance_report(self) -> Dict[str, Any]:
        """Gera relatório completo de performance da NPU"""
        current = self.get_current_metrics()
        averages = self.get_average_metrics()

        return {
            "current_metrics": {
                "utilization_percent": current.utilization_percent,
                "memory_used_mb": current.memory_used_mb,
                "temperature_celsius": current.temperature_celsius,
                "power_consumption_watts": current.power_consumption_watts,
                "inference_time_ms": current.inference_time_ms
            },
            "average_metrics_1min": averages,
            "performance_score": self._calculate_performance_score(current, averages),
            "optimization_suggestions": self._get_optimization_suggestions(current, averages),
            "timestamp": time.time()
        }

    def _calculate_performance_score(self, current: NPUMetrics, averages: Dict[str, float]) -> float:
        """Calcula score de performance da NPU (0-100)"""
        # Score baseado em eficiência energética e tempo de resposta
        utilization_score = min(current.utilization_percent / 80.0, 1.0) * 100
        power_efficiency = max(0, 100 - (current.power_consumption_watts * 10))
        response_time_score = max(0, 100 - (current.inference_time_ms - 40))

        return (utilization_score + power_efficiency + response_time_score) / 3

    def _get_optimization_suggestions(self, current: NPUMetrics, averages: Dict[str, float]) -> list[str]:
        """Gera sugestões de otimização baseadas nas métricas"""
        suggestions = []

        if current.utilization_percent < 50:
            suggestions.append("NPU subutilizada - considere aumentar batch size ou paralelização")

        if current.temperature_celsius > 70:
            suggestions.append("Temperatura elevada - verifique resfriamento e throttling")

        if current.power_consumption_watts > 15:
            suggestions.append("Alto consumo energético - considere otimização de modelo")

        if current.inference_time_ms > 100:
            suggestions.append("Tempo de inferência alto - considere quantização ou cache")

        if not suggestions:
            suggestions.append("Performance otimizada - mantendo monitoramento")

        return suggestions


# Instância global do monitor
npu_monitor = NPUMonitor()


@contextmanager
def monitor_inference():
    """Context manager para monitorar uma inferência específica"""
    start_time = time.time()
    start_metrics = npu_monitor.get_current_metrics()

    try:
        yield
    finally:
        end_time = time.time()
        end_metrics = npu_monitor.get_current_metrics()

        inference_time = (end_time - start_time) * 1000  # ms
        logger.info(".2f"
                   f"start_util: {start_metrics.utilization_percent:.1f}%, "
                   f"end_util: {end_metrics.utilization_percent:.1f}%, "
                   f"power: {end_metrics.power_consumption_watts:.2f}W")
