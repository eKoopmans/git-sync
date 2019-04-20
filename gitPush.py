### TODO:
# - location: command line argument
# - create a pull script

# Imports.
import os
import shutil
import fileinput
import subprocess
from git import Repo

# TODO: Make this a command-line argument.
location = 'work'
dryrun = False

# Setup variables.
local = r"C:\Users\eko\Desktop\Northcote High School\8. Git\TEST"
remote = {
  'work': r"Z:\Northcote High School\8. Git",
  'home': r"C:\Users\eko\Desktop\VIRTUAL\home"
}
ffs = r"C:\Program Files\FreeFileSync\FreeFileSync.exe"

# Get all dirs in local.
gitDirs = next(os.walk(local))[1]

# Loop through all dirs.
for project in gitDirs:
  # Progress update.
  print(project + ':', flush=True)

  # Check if it is a git project.
  localDir = os.path.join(local, project)
  try:
    localRepo = Repo(localDir)
  except:
    print('Not a repo.', flush=True)
    continue

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

  # Enable pushing directly to remote.
  with remoteRepo.config_writer() as cw:
    cw.set_value('receive', 'denyCurrentBranch', 'updateInstead')

  # Setup local repo to point to remote.
  try:
    localDest = localRepo.remote(location).set_url(remoteDir)
  except:
    localDest = localRepo.create_remote(location, remoteDir)

  # Push to remote.
  print('Pushing local to remote.', flush=True)
  if dryrun:
    infoList = localDest.push(['--all', '--follow-tags', '--dry-run'])
  else:
    infoList = localDest.push(['--all', '--follow-tags'])
  for info in infoList:
    print('\t{:10}:\t{}'.format(str(info.local_ref), info.summary.strip('\r\n')))

  # Progress update.
  print(project + ' done!\n', flush=True)

# Synchronise all .devel folders with FreeFileSync (FFS).
localDevel = os.path.join(localDir, '.devel')
if not dryrun and os.path.isdir(localDevel):
  # Setup paths.
  print('Syncing all .devel folders.', flush=True)
  ffsDevel = os.path.join(remote[location], 'gitDevel.ffs_batch')

  # Create the FFS sync file if it doesn't exist.
  if not os.path.exists(ffsDevel):
    shutil.copy2('./template.ffs_batch', ffsDevel)
    with fileinput.FileInput(ffsDevel, inplace=True) as file:
      for line in file:
        print(line.replace('%LOCAL%', local).replace('%REMOTE%', remote[location]), end='')

  # Run the sync.
  subprocess.call([ffs, ffsDevel])

# Progress update.
print('All done!', flush=True)
