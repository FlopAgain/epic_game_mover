import os
import shutil
import json
import glob
import subprocess
import sys
import time

def close_epic_launcher():
    print("Fermeture de l'Epic Games Launcher...")
    # Liste des processus à fermer
    processes = ["EpicGamesLauncher.exe", "UnrealCEFSubProcess.exe"]
    for process in processes:
        try:
            subprocess.run(["taskkill", "/F", "/IM", process], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"Processus {process} fermé.")
        except subprocess.CalledProcessError:
            print(f"Processus {process} n'était pas en cours d'exécution.")

def find_manifest(game_name):
    manifest_dir = r"C:\ProgramData\Epic\EpicGamesLauncher\Data\Manifests"
    manifest_files = glob.glob(os.path.join(manifest_dir, "*.item"))
    print(f"Recherche du manifeste pour le jeu '{game_name}' dans {manifest_dir}...")
    for manifest_file in manifest_files:
        try:
            with open(manifest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Supposons que le nom du jeu est dans la clé 'DisplayName' ou similaire
                if 'DisplayName' in data and game_name.lower() in data['DisplayName'].lower():
                    print(f"Manifeste trouvé : {manifest_file}")
                    return manifest_file, data
        except json.JSONDecodeError:
            print(f"Erreur de décodage JSON dans le fichier {manifest_file}.")
    print(f"Manifeste pour le jeu '{game_name}' non trouvé.")
    return None, None

def move_game_files(old_path, new_path):
    print(f"Déplacement des fichiers de {old_path} vers {new_path}...")
    if not os.path.exists(old_path):
        print(f"Le chemin source {old_path} n'existe pas.")
        return False
    try:
        shutil.move(old_path, new_path)
        print("Déplacement réussi.")
        return True
    except Exception as e:
        print(f"Erreur lors du déplacement : {e}")
        return False

def format_path(path):
    # Séparer le lecteur et le reste du chemin
    drive, tail = os.path.splitdrive(path)
    # Ajouter un double backslash après le lecteur
    drive = drive + '\\'
    # Supprimer les barres initiales du tail
    tail = tail.lstrip('\\/')
    # Remplacer les backslashes par des slashes dans le tail
    tail = tail.replace('\\', '/')
    # Combiner le drive et le tail
    formatted = drive + tail
    return formatted

def update_manifest(manifest_file, data, new_install_path):
    print("Mise à jour des chemins dans le manifeste...")
    # Mettre à jour les chemins avec le nom du dossier du jeu
    data['ManifestLocation'] = os.path.join(new_install_path, ".egstore")
    data['InstallLocation'] = new_install_path
    data['StagingLocation'] = os.path.join(new_install_path, ".egstore", "bps")
    
    # Reformatter les chemins selon les spécifications
    data['ManifestLocation'] = format_path(data['ManifestLocation'])
    data['InstallLocation'] = format_path(data['InstallLocation'])
    data['StagingLocation'] = format_path(data['StagingLocation'])
    
    try:
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print("Manifeste mis à jour et sauvegardé.")
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du manifeste : {e}")
        return False

def update_launcher_installed(game_name, new_install_path):
    launcher_file = r"C:\ProgramData\Epic\UnrealEngineLauncher\LauncherInstalled.dat"
    print(f"Mise à jour de {launcher_file}...")
    try:
        with open(launcher_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Parcourir les 'InstallationList' pour trouver le jeu
        updated = False
        for install in data.get('InstallationList', []):
            if 'AppName' in install and game_name.lower() in install['AppName'].lower():
                old_install = install.get('InstallLocation', '')
                install['InstallLocation'] = format_path(new_install_path)
                print(f"InstallLocation mis à jour de {old_install} à {install['InstallLocation']}.")
                updated = True
                break
        
        if not updated:
            print(f"Aucune entrée trouvée pour le jeu '{game_name}' dans {launcher_file}.")
            return False
        
        with open(launcher_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print("LauncherInstalled.dat mis à jour et sauvegardé.")
        return True
    except json.JSONDecodeError:
        print("Erreur de décodage JSON dans LauncherInstalled.dat.")
        return False
    except Exception as e:
        print(f"Erreur lors de la mise à jour de LauncherInstalled.dat : {e}")
        return False

def start_epic_launcher():
    print("Démarrage de l'Epic Games Launcher...")
    epic_path = r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe"
    if os.path.exists(epic_path):
        try:
            subprocess.Popen([epic_path])
            print("Epic Games Launcher démarré.")
        except Exception as e:
            print(f"Erreur lors du démarrage de l'Epic Games Launcher : {e}")
    else:
        print(f"Chemin de l'Epic Games Launcher non trouvé : {epic_path}")

def backup_file(file_path):
    backup_path = file_path + ".bak"
    try:
        shutil.copy(file_path, backup_path)
        print(f"Backup créé : {backup_path}")
    except Exception as e:
        print(f"Erreur lors de la création du backup de {file_path} : {e}")

def main():
    if not os.name == 'nt':
        print("Ce script est conçu pour Windows.")
        sys.exit(1)
    
    game_name = input("Entrez le nom du jeu à déplacer : ").strip()
    new_install_path = input("Entrez le nouveau chemin d'installation (par exemple D:\\Games\\test_game_mover\\) : ").strip()
    
    if not os.path.isabs(new_install_path):
        print("Veuillez entrer un chemin absolu valide.")
        sys.exit(1)
    
    # Assurer que le chemin utilise des backslashes
    new_install_path = os.path.normpath(new_install_path)
    
    # Fermer le launcher
    close_epic_launcher()
    time.sleep(2)  # Attendre un peu pour s'assurer que les processus sont fermés
    
    # Trouver le manifeste
    manifest_file, manifest_data = find_manifest(game_name)
    if not manifest_file:
        sys.exit(1)
    
    # Sauvegarder le manifeste
    backup_file(manifest_file)
    
    # Sauvegarder LauncherInstalled.dat
    launcher_file = r"C:\ProgramData\Epic\UnrealEngineLauncher\LauncherInstalled.dat"
    backup_file(launcher_file)
    
    # Obtenir l'ancien chemin d'installation
    old_install_path = manifest_data.get('InstallLocation', '')
    if not old_install_path:
        print("Chemin d'installation actuel non trouvé dans le manifeste.")
        sys.exit(1)
    
    # Obtenir le nom du dossier du jeu
    game_folder_name = os.path.basename(old_install_path.rstrip("\\/"))
    
    # Construire le nouveau chemin complet
    new_install_path_full = os.path.join(new_install_path, game_folder_name)
    
    # Déplacer les fichiers
    success = move_game_files(old_install_path, new_install_path_full)
    if not success:
        sys.exit(1)
    
    # Mettre à jour le manifeste
    success = update_manifest(manifest_file, manifest_data, new_install_path_full)
    if not success:
        sys.exit(1)
    
    # Mettre à jour LauncherInstalled.dat
    success = update_launcher_installed(game_name, new_install_path_full)
    if not success:
        sys.exit(1)
    
    # Relancer le launcher
    start_epic_launcher()
    print("Opération terminée avec succès.")

if __name__ == "__main__":
    main()