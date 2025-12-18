"""
NebulaGraph Lightweight Auto-Deployment Service

This service handles automatic download, installation, and management of NebulaGraph
without requiring Java or any other dependencies. Uses pure binary deployment.
"""

import os
import subprocess
import platform
import zipfile
import tarfile
import time
import shutil
import signal
from pathlib import Path
from typing import Optional, Dict, Any
import json

from ..config import settings


class NebulaDeploymentError(Exception):
    """Custom exception for NebulaGraph deployment errors"""
    pass


class NebulaDeployer:
    """
    Lightweight NebulaGraph deployment and management service
    
    Features:
    - Automatic download of NebulaGraph binary release
    - No Java or Docker required
    - Process management (start/stop/restart)
    - Health checks and monitoring
    - Configuration management
    """
    
    def __init__(self, base_dir: Path | str | None = None):
        """
        Initialize the deployer
        
        Args:
            base_dir: Base directory for NebulaGraph installation
        """
        self.base_dir = Path(base_dir or settings.NEBULA_DEPLOY_PATH).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # NebulaGraph configuration
        self.config = {
            "version": "v3.6.0",
            "edition": "community",
            "download_url_template": "https://github.com/vesoft-inc/nebula/releases/download/{version}/nebula-graph-{edition}-{version}-{platform}.{ext}",
            "ports": {
                "graph": settings.NEBULA_GRAPH_PORT if hasattr(settings, 'NEBULA_GRAPH_PORT') else 9669,
                "meta": settings.NEBULA_META_PORT if hasattr(settings, 'NEBULA_META_PORT') else 9559,
                "storage": settings.NEBULA_STORAGE_PORT if hasattr(settings, 'NEBULA_STORAGE_PORT') else 9779
            },
            "memory": {
                "rocksdb_block_cache": "256MB",
                "query_memory": "512MB"
            },
            "auth": {
                "user": settings.NEBULA_USER if hasattr(settings, 'NEBULA_USER') else "root",
                "password": settings.NEBULA_PASSWORD if hasattr(settings, 'NEBULA_PASSWORD') else "nebula"
            }
        }
        
        # Platform detection
        self.platform_info = self._detect_platform()
        
        # Paths
        self.install_dir = self.base_dir / f"nebula-graph-{self.config['edition']}-{self.config['version']}"
        self.bin_dir = self.install_dir / "bin"
        self.conf_dir = self.install_dir / "conf"
        self.data_dir = self.base_dir / "data"
        self.logs_dir = self.base_dir / "logs"
        self.pid_file = self.base_dir / "nebula.pid"
        
        # State
        self._is_installed = None
        self._is_running = None
    
    def _detect_platform(self) -> Dict[str, str]:
        """Detect current platform and architecture"""
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        # Map to NebulaGraph naming conventions
        if system == "windows":
            plat = "windows"
            ext = "zip"
        elif system == "linux":
            plat = "linux"
            ext = "tar.gz"
        elif system == "darwin":
            plat = "darwin"
            ext = "tar.gz"
        else:
            plat = system
            ext = "tar.gz"
        
        # Architecture mapping
        arch_map = {
            "x86_64": "x86_64",
            "amd64": "x86_64",
            "arm64": "aarch64",
            "aarch64": "aarch64"
        }
        
        arch = arch_map.get(machine, machine)
        
        return {
            "platform": f"{plat}-{arch}",
            "ext": ext,
            "python_system": system,
            "arch": arch
        }
    
    def _get_download_url(self) -> str:
        """Generate download URL for current platform"""
        url = self.config["download_url_template"].format(
            version=self.config["version"],
            edition=self.config["edition"],
            platform=self.platform_info["platform"],
            ext=self.platform_info["ext"]
        )
        return url
    
    def check_dependencies(self) -> bool:
        """Check if system has required dependencies (minimal for binary)"""
        # Only need basic system tools
        try:
            subprocess.run(["curl", "--version"], capture_output=True, timeout=5)
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
            try:
                subprocess.run(["wget", "--version"], capture_output=True, timeout=5)
                return True
            except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
                return False
    
    def check_nebula_installed(self) -> bool:
        """Check if NebulaGraph is already installed"""
        if self._is_installed is not None:
            return self._is_installed
        
        # Check if installation directory exists
        if self.install_dir.exists():
            # Check for nebula binaries
            nebula_bin = self.bin_dir / "nebula-metad"
            if nebula_bin.exists():
                self._is_installed = True
                return True
        
        self._is_installed = False
        return False
    
    def is_running(self) -> bool:
        """Check if NebulaGraph processes are running"""
        if not self.pid_file.exists():
            return False
        
        try:
            pid_data = json.loads(self.pid_file.read_text())
            
            # Check each process
            processes = ["nebula-metad", "nebula-graphd", "nebula-storaged"]
            for proc in processes:
                if proc in pid_data:
                    pid = pid_data[proc]
                    try:
                        if self.platform_info["python_system"] == "windows":
                            result = subprocess.run(
                                ["tasklist", "/FI", f"PID eq {pid}"],
                                capture_output=True,
                                text=True
                            )
                            if str(pid) not in result.stdout:
                                return False
                        else:
                            os.kill(pid, 0)
                    except (ProcessLookupError, OSError):
                        return False
            
            return True
            
        except (ValueError, Exception):
            return False
    
    def download_nebula(self, progress_callback=None) -> str:
        """
        Download NebulaGraph binary release
        
        Returns:
            Path to downloaded archive
            
        Raises:
            NebulaDeploymentError: If download fails
        """
        if not self.check_dependencies():
            raise NebulaDeploymentError(
                "System missing curl/wget. Please install curl or wget."
            )
        
        url = self._get_download_url()
        filename = url.split('/')[-1]
        archive_path = self.base_dir / "cache" / filename
        
        print(f"📥 Downloading NebulaGraph from {url}...")
        
        try:
            # Try curl first, then wget
            try:
                result = subprocess.run(
                    ["curl", "-L", "-o", str(archive_path), url],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    raise Exception(f"curl failed: {result.stderr}")
            except Exception:
                # Fallback to wget
                result = subprocess.run(
                    ["wget", "-O", str(archive_path), url],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    raise Exception(f"wget failed: {result.stderr}")
            
            # Verify download
            if not archive_path.exists() or archive_path.stat().st_size < 1000000:
                raise NebulaDeploymentError("Download failed or file too small")
            
            print(f"✅ Download completed: {archive_path}")
            return str(archive_path)
            
        except Exception as e:
            raise NebulaDeploymentError(f"Failed to download NebulaGraph: {e}")
    
    def extract_nebula(self, archive_path: str|Path) -> bool:
        """
        Extract NebulaGraph archive to installation directory
        
        Args:
            archive_path: Path to downloaded archive
            
        Returns:
            bool: Success status
        """
        print(f"📦 Extracting NebulaGraph to {self.base_dir}...")
        
        try:
            archive_path = Path(archive_path)
            
            if archive_path.suffix == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(self.base_dir)
            elif archive_path.suffixes == ['.tar', '.gz'] or archive_path.suffix == '.gz':
                with tarfile.open(archive_path, 'r:gz') as tar:
                    tar.extractall(self.base_dir)
            else:
                raise NebulaDeploymentError(f"Unsupported archive format: {archive_path}")
            
            # Find extracted directory (NebulaGraph usually extracts to a versioned folder)
            extracted_folders = [f for f in self.base_dir.iterdir() if f.is_dir() and f.name.startswith("nebula-graph")]
            if extracted_folders:
                # Rename to standardized name if needed
                extracted = extracted_folders[0]
                if extracted != self.install_dir and extracted.exists():
                    shutil.move(str(extracted), str(self.install_dir))
            
            print("✅ Extraction completed")
            
            # Verify installation
            if not self.check_nebula_installed():
                raise NebulaDeploymentError("Extraction completed but NebulaGraph installation not found")
            
            return True
            
        except Exception as e:
            raise NebulaDeploymentError(f"Failed to extract NebulaGraph: {e}")
    
    def configure_nebula(self) -> bool:
        """
        Configure NebulaGraph with optimized settings
        
        Returns:
            bool: Success status
        """
        print("⚙️ Configuring NebulaGraph...")
        
        try:
            # Create data and logs directories
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.logs_dir.mkdir(parents=True, exist_ok=True)
            
            # Configure metad
            meta_conf = self.conf_dir / "nebula-metad.conf"
            if meta_conf.exists():
                content = meta_conf.read_text()
                # Update paths
                content = content.replace("data_path=/var/lib/nebula/meta", f"data_path={self.data_dir}/meta")
                content = content.replace("log_path=/var/log/nebula", f"log_path={self.logs_dir}")
                # Update port
                content = content.replace("port=9559", f"port={self.config['ports']['meta']}")
                meta_conf.write_text(content)
            
            # Configure graphd
            graph_conf = self.conf_dir / "nebula-graphd.conf"
            if graph_conf.exists():
                content = graph_conf.read_text()
                content = content.replace("log_path=/var/log/nebula", f"log_path={self.logs_dir}")
                content = content.replace("port=9669", f"port={self.config['ports']['graph']}")
                graph_conf.write_text(content)
            
            # Configure storaged
            storage_conf = self.conf_dir / "nebula-storaged.conf"
            if storage_conf.exists():
                content = storage_conf.read_text()
                content = content.replace("data_path=/var/lib/nebula/storage", f"data_path={self.data_dir}/storage")
                content = content.replace("log_path=/var/log/nebula", f"log_path={self.logs_dir}")
                content = content.replace("port=9779", f"port={self.config['ports']['storage']}")
                storage_conf.write_text(content)
            
            # Create nebula.conf for client connections (optional)
            client_conf = self.conf_dir / "nebula.conf"
            client_config = {
                "hosts": [f"127.0.0.1:{self.config['ports']['graph']}"],
                "user": self.config["auth"]["user"],
                "password": self.config["auth"]["password"],
                "timeout": 1000
            }
            client_conf.write_text(json.dumps(client_config, indent=2))
            
            print("✅ Configuration completed")
            return True
            
        except Exception as e:
            raise NebulaDeploymentError(f"Failed to configure NebulaGraph: {e}")
    
    def start(self, wait_for_ready: bool = True, timeout: int = 60) -> bool:
        """
        Start NebulaGraph services
        
        Args:
            wait_for_ready: Whether to wait for services to be ready
            timeout: Maximum wait time in seconds
            
        Returns:
            bool: Success status
        """
        if self.is_running():
            print("NebulaGraph is already running")
            return True
        
        print("🚀 Starting NebulaGraph services...")
        
        try:
            # Start metad first
            meta_cmd = [str(self.bin_dir / "nebula-metad"), "--config", str(self.conf_dir / "nebula-metad.conf")]
            meta_proc = subprocess.Popen(
                meta_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(2)  # Wait for metad to start
            
            # Start storaged
            storage_cmd = [str(self.bin_dir / "nebula-storaged"), "--config", str(self.conf_dir / "nebula-storaged.conf")]
            storage_proc = subprocess.Popen(
                storage_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(2)  # Wait for storaged to start
            
            # Start graphd
            graph_cmd = [str(self.bin_dir / "nebula-graphd"), "--config", str(self.conf_dir / "nebula-graphd.conf")]
            graph_proc = subprocess.Popen(
                graph_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Save PIDs
            pids = {
                "nebula-metad": meta_proc.pid,
                "nebula-storaged": storage_proc.pid,
                "nebula-graphd": graph_proc.pid
            }
            self.pid_file.write_text(json.dumps(pids, indent=2))
            
            print("✅ NebulaGraph services started")
            
            if wait_for_ready:
                return self.wait_for_ready(timeout)
            
            return True
            
        except Exception as e:
            raise NebulaDeploymentError(f"Failed to start NebulaGraph: {e}")
    
    def stop(self) -> bool:
        """Stop NebulaGraph services"""
        if not self.is_running():
            print("NebulaGraph is not running")
            return True
        
        print("⏹️ Stopping NebulaGraph services...")
        
        try:
            if not self.pid_file.exists():
                return False
            
            pids = json.loads(self.pid_file.read_text())
            
            for proc_name, pid in pids.items():
                try:
                    if self.platform_info["python_system"] == "windows":
                        subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
                    else:
                        os.kill(pid, signal.SIGTERM)
                        time.sleep(1)
                        # Force kill if still running
                        try:
                            os.kill(pid, 0)
                            sigkill = getattr(signal, "SIGKILL", None)
                            if sigkill is not None:
                                os.kill(pid, sigkill)
                            else:
                                # SIGKILL may not be available on some platforms (e.g., Windows); try SIGTERM again
                                try:
                                    os.kill(pid, signal.SIGTERM)
                                except Exception:
                                    pass
                        except ProcessLookupError:
                            pass
                except (ProcessLookupError, OSError):
                    pass
            
            # Remove PID file
            if self.pid_file.exists():
                self.pid_file.unlink()
            
            print("✅ NebulaGraph services stopped")
            return True
            
        except Exception as e:
            print(f"⚠️ Error stopping NebulaGraph: {e}")
            return False
    
    def wait_for_ready(self, timeout: int = 60) -> bool:
        """
        Wait for NebulaGraph to be ready
        
        Args:
            timeout: Maximum wait time in seconds
            
        Returns:
            bool: True if ready, False if timeout
        """
        print("⏳ Waiting for NebulaGraph to be ready...")
        
        start_time = time.time()
        graph_port = self.config['ports']['graph']
        
        while time.time() - start_time < timeout:
            try:
                # Try to connect using nebula console
                result = subprocess.run(
                    [str(self.bin_dir / "nebula"), "-u", self.config['auth']['user'], 
                     "-p", self.config['auth']['password'], 
                     "--addr", f"127.0.0.1:{graph_port}",
                     "--cmd", "SHOW SPACES"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    print("✅ NebulaGraph is ready!")
                    return True
                    
            except Exception:
                pass
            
            time.sleep(2)
        
        print("❌ Timeout waiting for NebulaGraph")
        return False
    
    def initialize_database(self) -> bool:
        """
        Initialize database with default space and schema
        
        Returns:
            bool: Success status
        """
        print("🔧 Initializing database...")
        
        try:
            # Use nebula console to initialize
            graph_port = self.config['ports']['graph']
            
            # Create default space
            init_commands = [
                "CREATE SPACE IF NOT EXISTS memexia (partition_num=10, replica_factor=1)",
                "USE memexia",
                "CREATE TAG IF NOT EXISTS Node(id string, content string, node_type string, knowledge_base_id string, created_at string, updated_at string)",
                "CREATE EDGE IF NOT EXISTS RELATED(id string, type string, weight int)",
                "CREATE INDEX IF NOT EXISTS ON Node(id)",
                "CREATE INDEX IF NOT EXISTS ON Node(knowledge_base_id)",
                "CREATE INDEX IF NOT EXISTS ON Node(node_type)",
                "CREATE INDEX IF NOT EXISTS ON RELATED(id)"
            ]
            
            for cmd in init_commands:
                result = subprocess.run(
                    [str(self.bin_dir / "nebula"), "-u", self.config['auth']['user'], 
                     "-p", self.config['auth']['password'], 
                     "--addr", f"127.0.0.1:{graph_port}",
                     "--cmd", cmd],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0 and "already exists" not in result.stdout:
                    print(f"⚠️ Command failed: {cmd}")
                    print(f"Output: {result.stdout}")
                    print(f"Error: {result.stderr}")
            
            print("✅ Database initialized")
            return True
            
        except Exception as e:
            print(f"⚠️ Database initialization had issues: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check
        
        Returns:
            dict: Health status information
        """
        result = {
            "installed": self.check_nebula_installed(),
            "running": self.is_running(),
            "dependencies": self.check_dependencies(),
            "config": self.config
        }
        
        if self.is_running():
            try:
                # Check each service
                graph_port = self.config['ports']['graph']
                
                # Test connection
                result_test = subprocess.run(
                    [str(self.bin_dir / "nebula"), "-u", self.config['auth']['user'], 
                     "-p", self.config['auth']['password'], 
                     "--addr", f"127.0.0.1:{graph_port}",
                     "--cmd", "SHOW SPACES"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                result["database_connectivity"] = result_test.returncode == 0
                result["version"] = self.config['version']
                
            except Exception as e:
                result["database_connectivity"] = False
                result["error"] = str(e)
        
        return result
    
    def deploy(self) -> bool:
        """
        Complete deployment process
        
        Returns:
            bool: Success status
        """
        print("=" * 60)
        print("NebulaGraph Lightweight Deployment")
        print("=" * 60)
        
        # Step 1: Check dependencies
        if not self.check_dependencies():
            print("❌ Missing system dependencies (curl or wget)")
            print("Please install curl or wget:")
            print("  - Windows: Download curl from https://curl.se/windows/")
            print("  - Linux: sudo apt install curl")
            print("  - macOS: brew install curl")
            return False
        
        # Step 2: Check if already installed
        if self.check_nebula_installed():
            print("✅ NebulaGraph is already installed")
        else:
            # Step 3: Download
            try:
                archive_path = self.download_nebula()
            except NebulaDeploymentError as e:
                print(f"❌ Download failed: {e}")
                return False
            
            # Step 4: Extract
            try:
                self.extract_nebula(archive_path)
            except NebulaDeploymentError as e:
                print(f"❌ Extraction failed: {e}")
                return False
        
        # Step 5: Configure
        try:
            self.configure_nebula()
        except NebulaDeploymentError as e:
            print(f"❌ Configuration failed: {e}")
            return False
        
        # Step 6: Start
        try:
            if not self.start():
                print("❌ Failed to start NebulaGraph")
                return False
        except NebulaDeploymentError as e:
            print(f"❌ Start failed: {e}")
            return False
        
        # Step 7: Initialize
        self.initialize_database()
        
        # Step 8: Health check
        health = self.health_check()
        print("\n📊 Deployment Status:")
        print(f"  Installed: {health['installed']}")
        print(f"  Running: {health['running']}")
        print(f"  Database Connectivity: {health.get('database_connectivity', 'Unknown')}")
        print(f"  Graph Port: {self.config['ports']['graph']}")
        print(f"  Meta Port: {self.config['ports']['meta']}")
        print(f"  Storage Port: {self.config['ports']['storage']}")
        print(f"  User: {self.config['auth']['user']}")
        print(f"  Password: {'*' * 8}")
        
        print("\n" + "=" * 60)
        print("✅ Deployment completed successfully!")
        print("=" * 60)
        
        return True
    
    def cleanup(self) -> bool:
        """Remove NebulaGraph installation and data"""
        print("🧹 Cleaning up NebulaGraph installation...")
        
        try:
            # Stop if running
            if self.is_running():
                self.stop()
            
            # Remove installation directory
            if self.install_dir.exists():
                shutil.rmtree(self.install_dir)
            
            # Remove data and logs (optional - ask user)
            if self.data_dir.exists() or self.logs_dir.exists():
                print("⚠️  Data and logs directories found:")
                print(f"  Data: {self.data_dir}")
                print(f"  Logs: {self.logs_dir}")
                confirm = input("Remove data and logs as well? [y/N]: ")
                if confirm.lower() in ['y', 'yes']:
                    if self.data_dir.exists():
                        shutil.rmtree(self.data_dir)
                    if self.logs_dir.exists():
                        shutil.rmtree(self.logs_dir)
            
            # Remove PID file
            if self.pid_file.exists():
                self.pid_file.unlink()
            
            print("✅ Cleanup completed")
            return True
            
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
            return False


# Global instance
_nebula_deployer: Optional[NebulaDeployer] = None


def get_nebula_deployer() -> NebulaDeployer:
    """Get or create global Nebula deployer instance"""
    global _nebula_deployer
    if _nebula_deployer is None:
        _nebula_deployer = NebulaDeployer()
    return _nebula_deployer


def auto_deploy_nebula() -> bool:
    """
    Auto-deploy NebulaGraph on application startup
    
    Returns:
        bool: Success status
    """
    deployer = get_nebula_deployer()
    
    # Check if already running
    if deployer.is_running():
        return True
    
    # Check if installed but not running
    if deployer.check_nebula_installed():
        print("NebulaGraph is installed but not running, attempting to start...")
        try:
            return deployer.start()
        except Exception as e:
            print(f"Failed to start NebulaGraph: {e}")
            return False
    
    # Full deployment
    return deployer.deploy()


if __name__ == "__main__":
    # Command line interface
    import argparse
    
    parser = argparse.ArgumentParser(description="NebulaGraph Lightweight Deployer")
    parser.add_argument("action", choices=["deploy", "start", "stop", "status", "cleanup"], 
                       help="Action to perform")
    
    args = parser.parse_args()
    
    deployer = get_nebula_deployer()
    
    if args.action == "deploy":
        deployer.deploy()
    elif args.action == "start":
        deployer.start()
    elif args.action == "stop":
        deployer.stop()
    elif args.action == "status":
        health = deployer.health_check()
        print(json.dumps(health, indent=2))
    elif args.action == "cleanup":
        deployer.cleanup()
