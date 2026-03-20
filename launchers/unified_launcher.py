"""
==========================================================
JARVIS UNIFIED LAUNCHER - PhD-Level System Orchestration
==========================================================
Manages all three services with proper lifecycle:
1. gRPC Server (port 50051)
2. Main Orchestrator (port 8000)
3. WhatsApp Bridge (port 3000)

Features:
- Graceful startup/shutdown
- Health monitoring
- Auto-restart on failure
- Distributed logging
- Process supervision
==========================================================
"""

import subprocess
import sys
import os
import time
import signal
import logging
import asyncio
import psutil
from typing import Dict, List, Optional
from datetime import datetime
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/unified_launcher.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Fix Windows console encoding
import sys
if sys.platform == 'win32':
    import codecs
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


class ServiceManager:
    """Manages a single service process"""

    def __init__(self, name: str, command: List[str], cwd: str = None, env: Dict = None):
        self.name = name
        self.command = command
        self.cwd = cwd or os.getcwd()
        self.env = env or os.environ.copy()
        self.process: Optional[subprocess.Popen] = None
        self.start_time: Optional[datetime] = None
        self.restart_count = 0
        self.max_restarts = 5
        self.restart_window = 300  # 5 minutes

    def start(self) -> bool:
        """Start the service"""
        try:
            logger.info(f"🚀 Starting {self.name}...")
            logger.info(f"   Command: {' '.join(self.command)}")
            logger.info(f"   CWD: {self.cwd}")

            self.process = subprocess.Popen(
                self.command,
                cwd=self.cwd,
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            self.start_time = datetime.now()
            time.sleep(2)  # Give it time to start

            if self.is_running():
                logger.info(f"✅ {self.name} started (PID: {self.process.pid})")
                return True
            else:
                logger.error(f"❌ {self.name} failed to start")
                return False

        except Exception as e:
            logger.error(f"❌ Error starting {self.name}: {e}")
            return False

    def stop(self, timeout: int = 10) -> bool:
        """Stop the service gracefully"""
        if not self.process:
            return True

        try:
            logger.info(f"🛑 Stopping {self.name}...")

            # Try graceful shutdown first
            if sys.platform == 'win32':
                self.process.send_signal(signal.CTRL_C_EVENT)
            else:
                self.process.send_signal(signal.SIGTERM)

            try:
                self.process.wait(timeout=timeout)
                logger.info(f"✅ {self.name} stopped gracefully")
                return True
            except subprocess.TimeoutExpired:
                logger.warning(f"⚠️ {self.name} did not stop gracefully, forcing...")
                self.process.kill()
                self.process.wait()
                logger.info(f"✅ {self.name} force stopped")
                return True

        except Exception as e:
            logger.error(f"❌ Error stopping {self.name}: {e}")
            return False

    def is_running(self) -> bool:
        """Check if service is running"""
        if not self.process:
            return False

        return self.process.poll() is None

    def get_status(self) -> Dict:
        """Get service status"""
        if not self.is_running():
            return {
                "name": self.name,
                "status": "stopped",
                "pid": None,
                "uptime": None,
                "restart_count": self.restart_count
            }

        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0

        try:
            proc = psutil.Process(self.process.pid)
            cpu_percent = proc.cpu_percent(interval=0.1)
            memory_mb = proc.memory_info().rss / 1024 / 1024
        except:
            cpu_percent = 0
            memory_mb = 0

        return {
            "name": self.name,
            "status": "running",
            "pid": self.process.pid,
            "uptime": uptime,
            "restart_count": self.restart_count,
            "cpu_percent": cpu_percent,
            "memory_mb": memory_mb
        }

    def should_restart(self) -> bool:
        """Check if service should be restarted"""
        if self.restart_count >= self.max_restarts:
            logger.error(f"❌ {self.name} exceeded max restarts ({self.max_restarts})")
            return False

        return True

    def restart(self) -> bool:
        """Restart the service"""
        logger.info(f"🔄 Restarting {self.name}...")
        self.restart_count += 1
        self.stop()
        time.sleep(2)
        return self.start()


class UnifiedLauncher:
    """Unified launcher for all JARVIS services"""

    def __init__(self):
        self.services: Dict[str, ServiceManager] = {}
        self.running = False
        self.start_time = datetime.now()

        # Ensure directories exist
        os.makedirs("logs", exist_ok=True)

    def setup_services(self):
        """Setup all services"""
        logger.info("="*60)
        logger.info("JARVIS UNIFIED LAUNCHER - PhD-Level Orchestration")
        logger.info("="*60)

        # Service 1: gRPC Server
        self.services['grpc'] = ServiceManager(
            name="gRPC Server",
            command=[sys.executable, "grpc_service/python_server.py"],
            cwd=os.getcwd()
        )

        # Service 2: Main Orchestrator (deterministic selection)
        if os.path.exists("main.py"):
            orchestrator_file = "main.py"
            logger.info("📌 Using JARVIS main orchestrator")
        elif os.path.exists("jarvis_brain.py"):
            orchestrator_file = "jarvis_brain.py"
            logger.info("📌 Using JARVIS brain fallback")
        else:
            raise FileNotFoundError("No supported orchestrator entrypoint found (main.py or jarvis_brain.py)")

        self.services['orchestrator'] = ServiceManager(
            name="Main Orchestrator",
            command=[sys.executable, orchestrator_file],
            cwd=os.getcwd()
        )

        # Service 3: WhatsApp Bridge
        self.services['whatsapp'] = ServiceManager(
            name="WhatsApp Bridge",
            command=["node", "whatsapp/baileys_bridge.js"],
            cwd=os.getcwd()
        )

        # Service 4: MCP Terminal Server (Optional)
        if os.path.exists("mcp/server.js"):
            self.services['mcp'] = ServiceManager(
                name="MCP Terminal Server",
                command=["node", "mcp/server.js"],
                cwd=os.getcwd()
            )
            logger.info("📌 MCP Terminal Server available")

    def start_all(self):
        """Start all services in order"""
        logger.info("\n🚀 Starting all services...")

        # Start in dependency order (critical services)
        critical_services = ['grpc', 'orchestrator', 'whatsapp']

        # Optional services (won't abort if they fail)
        optional_services = []
        if 'mcp' in self.services:
            optional_services.append('mcp')

        # Start critical services
        for service_name in critical_services:
            service = self.services[service_name]
            if not service.start():
                logger.error(f"❌ Failed to start {service_name}, aborting...")
                self.stop_all()
                return False

            # Wait between services
            time.sleep(3)

        # Start optional services (don't abort on failure)
        for service_name in optional_services:
            service = self.services[service_name]
            if not service.start():
                logger.warning(f"⚠️ Optional service {service_name} failed to start, continuing...")
            else:
                time.sleep(3)

        self.running = True
        logger.info("\n✅ All critical services started successfully!")
        self.print_status()
        return True

    def stop_all(self):
        """Stop all services"""
        logger.info("\n🛑 Stopping all services...")
        self.running = False

        # Stop in reverse order
        stop_order = ['mcp', 'whatsapp', 'orchestrator', 'grpc']
        for service_name in stop_order:
            if service_name in self.services:
                self.services[service_name].stop()

        logger.info("✅ All services stopped")

    def monitor_loop(self):
        """Monitor services and restart if needed"""
        logger.info("\n👁️ Starting monitoring loop...")

        try:
            while self.running:
                time.sleep(10)  # Check every 10 seconds

                for name, service in self.services.items():
                    if not service.is_running():
                        logger.warning(f"⚠️ {name} is not running!")

                        if service.should_restart():
                            logger.info(f"🔄 Auto-restarting {name}...")
                            if not service.restart():
                                logger.error(f"❌ Failed to restart {name}")
                        else:
                            logger.error(f"❌ {name} cannot be restarted (max attempts reached)")
                            self.running = False
                            break

        except KeyboardInterrupt:
            logger.info("\n⚠️ Received interrupt signal")
        finally:
            self.stop_all()

    def print_status(self):
        """Print status of all services"""
        logger.info("\n" + "="*60)
        logger.info("SERVICE STATUS")
        logger.info("="*60)

        for name, service in self.services.items():
            status = service.get_status()
            if status['status'] == 'running':
                logger.info(f"✅ {status['name']}")
                logger.info(f"   PID: {status['pid']}")
                logger.info(f"   Uptime: {status['uptime']:.1f}s")
                logger.info(f"   CPU: {status['cpu_percent']:.1f}%")
                logger.info(f"   Memory: {status['memory_mb']:.1f}MB")
            else:
                logger.info(f"❌ {status['name']} - STOPPED")

        logger.info("="*60)

    def run(self):
        """Main run method"""
        self.setup_services()

        if not self.start_all():
            logger.error("❌ Failed to start services")
            return 1

        # Setup signal handlers
        signal.signal(signal.SIGINT, lambda s, f: self.stop_all())
        signal.signal(signal.SIGTERM, lambda s, f: self.stop_all())

        # Start monitoring
        self.monitor_loop()

        return 0


if __name__ == "__main__":
    launcher = UnifiedLauncher()
    sys.exit(launcher.run())
