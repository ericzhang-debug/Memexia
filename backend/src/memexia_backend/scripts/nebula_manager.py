#!/usr/bin/env python3
"""
NebulaGraph Lightweight Deployment Manager

Command line tool for managing NebulaGraph deployment without Java.
Usage:
    python nebula_manager.py deploy     # Full deployment
    python nebula_manager.py start      # Start NebulaGraph
    python nebula_manager.py stop       # Stop NebulaGraph
    python nebula_manager.py status     # Check status
    python nebula_manager.py cleanup    # Remove installation
"""

import sys
import os
import subprocess

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from memexia_backend.services.nebula_deployer import NebulaDeployer
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="NebulaGraph Lightweight Deployment Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python nebula_manager.py deploy      # Full deployment
  python nebula_manager.py start       # Start NebulaGraph
  python nebula_manager.py stop        # Stop NebulaGraph
  python nebula_manager.py status      # Check status
  python nebula_manager.py cleanup     # Remove installation
  python nebula_manager.py health      # Detailed health check
        """
    )
    
    parser.add_argument(
        "action",
        choices=["deploy", "start", "stop", "status", "cleanup", "health", "init"],
        help="Action to perform"
    )
    
    parser.add_argument(
        "--dir",
        help="Custom installation directory (default: backend/nebula)"
    )
    
    parser.add_argument(
        "--graph-port",
        type=int,
        default=9669,
        help="Graph service port (default: 9669)"
    )
    
    parser.add_argument(
        "--meta-port",
        type=int,
        default=9559,
        help="Meta service port (default: 9559)"
    )
    
    parser.add_argument(
        "--storage-port",
        type=int,
        default=9779,
        help="Storage service port (default: 9779)"
    )
    
    parser.add_argument(
        "--version",
        default="v3.6.0",
        help="NebulaGraph version to install (default: v3.6.0)"
    )
    
    args = parser.parse_args()
    
    # Create deployer with custom settings
    deployer = NebulaDeployer(base_dir=args.dir)
    deployer.config["ports"]["graph"] = args.graph_port
    deployer.config["ports"]["meta"] = args.meta_port
    deployer.config["ports"]["storage"] = args.storage_port
    deployer.config["version"] = args.version
    
    # Handle actions
    if args.action == "deploy":
        print("=" * 60)
        print("NebulaGraph Lightweight Deployment")
        print("=" * 60)
        success = deployer.deploy()
        sys.exit(0 if success else 1)
    
    elif args.action == "start":
        try:
            if deployer.start():
                print("✅ NebulaGraph started successfully")
                sys.exit(0)
            else:
                print("❌ Failed to start NebulaGraph")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
    
    elif args.action == "stop":
        if deployer.stop():
            print("✅ NebulaGraph stopped successfully")
            sys.exit(0)
        else:
            print("❌ Failed to stop NebulaGraph")
            sys.exit(1)
    
    elif args.action == "status":
        health = deployer.health_check()
        print("\n📊 NebulaGraph Status:")
        print(f"  Installed: {health['installed']}")
        print(f"  Running: {health['running']}")
        print(f"  Dependencies: {health['dependencies']}")
        
        if health['running']:
            print(f"  Graph Port: {deployer.config['ports']['graph']}")
            print(f"  Meta Port: {deployer.config['ports']['meta']}")
            print(f"  Storage Port: {deployer.config['ports']['storage']}")
            print(f"  Version: {deployer.config['version']}")
            
            if 'database_connectivity' in health:
                print(f"  Database Connectivity: {health['database_connectivity']}")
        
        sys.exit(0)
    
    elif args.action == "health":
        import json
        health = deployer.health_check()
        if deployer.is_running():
            try:
                # Add detailed database info
                result = subprocess.run(
                    [str(deployer.bin_dir / "nebula"), "-u", deployer.config['auth']['user'], 
                     "-p", deployer.config['auth']['password'], 
                     "--addr", f"127.0.0.1:{deployer.config['ports']['graph']}",
                     "--cmd", "SHOW SPACES"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    health['spaces'] = result.stdout.strip()
                
                # Get version info
                version_result = subprocess.run(
                    [str(deployer.bin_dir / "nebula"), "-u", deployer.config['auth']['user'], 
                     "-p", deployer.config['auth']['password'], 
                     "--addr", f"127.0.0.1:{deployer.config['ports']['graph']}",
                     "--cmd", "SHOW META VERSION"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if version_result.returncode == 0:
                    health['meta_version'] = version_result.stdout.strip()
                    
            except Exception as e:
                health['connection_error'] = str(e)
        
        print(json.dumps(health, indent=2))
        sys.exit(0)
    
    elif args.action == "cleanup":
        confirm = input("Are you sure you want to remove NebulaGraph installation? [y/N]: ")
        if confirm.lower() in ['y', 'yes']:
            if deployer.cleanup():
                print("✅ Cleanup completed")
                sys.exit(0)
            else:
                print("❌ Cleanup failed")
                sys.exit(1)
        else:
            print("❌ Cleanup cancelled")
            sys.exit(1)
    
    elif args.action == "init":
        # Initialize only configuration (no download)
        print("🔧 Initializing NebulaGraph configuration...")
        try:
            if not deployer.check_nebula_installed():
                print("❌ NebulaGraph not installed. Run 'deploy' first.")
                sys.exit(1)
            
            deployer.configure_nebula()
            print("✅ Configuration initialized")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
