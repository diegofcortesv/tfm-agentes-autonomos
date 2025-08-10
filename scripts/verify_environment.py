import sys
import subprocess
import importlib.util

def check_python_version():
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} (necesita 3.9+)")
        return False

def check_command(command, name):
    try:
        result = subprocess.run([command, '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ {name}: {result.stdout.strip().split()[0]}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"❌ {name}: No encontrado")
        return False

def check_package(package, name=None):
    name = name or package
    if importlib.util.find_spec(package):
        print(f"✅ {name}: Instalado")
        return True
    else:
        print(f"❌ {name}: No instalado")
        return False

def main():
    print("=== Verificación del Entorno de Desarrollo ===\n")
    
    checks = []
    
    # Verificar Python
    checks.append(check_python_version())
    
    # Verificar comandos
    checks.append(check_command('git', 'Git'))
    checks.append(check_command('gcloud', 'Google Cloud SDK'))
    checks.append(check_command('docker', 'Docker'))
    
    # Verificar paquetes Python básicos
    checks.append(check_package('pip'))
    checks.append(check_package('venv'))
    
    print(f"\n=== Resultado: {sum(checks)}/{len(checks)} verificaciones exitosas ===")
    
    if all(checks):
        print("🎉 Entorno listo para desarrollo!")
    else:
        print("⚠️  Faltan algunos componentes. Revisar elementos marcados con ❌")

if __name__ == "__main__":
    main()