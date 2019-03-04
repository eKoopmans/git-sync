### TODO:
# - location: command line argument
# - add ability for work to push (and pull) to bare
# - create a pull script

# Imports.
import os
import shutil
import fileinput
import subprocess
from git import Repo

# TODO: Make this a command-line argument.
location = 'work'

# Setup variables.
local = r"C:\Users\eko\Desktop\Northcote High School\8. Git\TEST"
bare = {
  'work': r"Z:\git-bare",
  'home': r"C:\Users\eko\Desktop\VIRTUAL\bare-home"
}
remote = {
  'work': r"Z:\Northcote High School\8. Git",
  'home': r"C:\Users\eko\Desktop\VIRTUAL\remote-home"
}
ffs = r"C:\Program Files\FreeFileSync\FreeFileSync.exe"

# Get all dirs in local.
gitDirs = next(os.walk(local))[1]

# Loop through all dirs.
for project in gitDirs:
  # Progress update.
  print(project + ':')

  # Check if it is a git project.
  localDir = os.path.join(local, project)
  try:
    localRepo = Repo(localDir)
  except:
    print('Not a repo.')
    continue

  # Setup the bare directory if necessary.
  bareDir = os.path.join(bare[location], project + '.git')
  if not os.path.isdir(bareDir):
    bare_repo = Repo.init(bareDir, bare=True)
    # assert bare_repo.bare

  # Push to bare remote.
  print('Pushing local to bare.')
  try:
    localDest = localRepo.remote(location)
  except:
    localDest = localRepo.create_remote(location, bareDir)
  localDest.push()

  # Setup the remote directory if necessary.
  remoteDir = os.path.join(remote[location], project)
  try:
    os.makedirs(remoteDir)
  except:
    pass

  # Setup the remote repo if necessary.
  try:
    remoteRepo = Repo(remoteDir)
  except:
    remoteRepo = Repo.init(remoteDir)

  # Pull remote from bare.
  print('Pulling remote from bare.')
  try:
    remoteSrc = remoteRepo.remote(location)
  except:
    remoteSrc = remoteRepo.create_remote(location, bareDir)
  remoteSrc.pull('master')

  # Synchronise .devel folder with FreeFileSync (FFS).
  localDevel = os.path.join(localDir, '.devel')
  if os.path.isdir(localDevel):
    # Setup paths.
    print('Syncing .devel.')
    remoteDevel = os.path.join(remoteDir, '.devel')
    ffsDevel = os.path.join(bare[location], project + '.ffs_batch')

    # Create the FFS sync file if it doesn't exist.
    if not os.path.exists(ffsDevel):
      shutil.copy2('./template.ffs_batch', ffsDevel)
      with fileinput.FileInput(ffsDevel, inplace=True) as file:
        for line in file:
          print(line.replace('%LOCAL%', localDevel).replace('%REMOTE%', remoteDevel), end='')

    # Run the sync.
    subprocess.call([ffs, ffsDevel])

  # Progress update.
  print(project + ' done!')
