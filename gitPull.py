### TODO:
# - change behaviour to scan remote, not local, for projects
#   - and clone projects that don't exist locally
# - THIS AND GITPUSH:
#   - add a way to NOT overwrite the remote location (on this and gitPush)
#   - specify individual projects to push/pull (instead of all)
#     - might require modifying the .devel sync...

# Imports.
import os
import shutil
import fileinput
import subprocess
from git import Repo
from argparse import ArgumentParser

# Setup command-line arguments.
parser = ArgumentParser(description='Pull all specified Git projects from a remote location.')
parser.add_argument('local', metavar='LOCAL', nargs='?', default='.',
                    help='The local root of the projects (default: current dir)')
parser.add_argument('projects', metavar='PROJECT', nargs='*',
                    help='The names of each project to run (default: * in local)')
parser.add_argument('-l', '--location', dest='location', metavar='LOCATION', default='work',
                    help='Remote location (work or home)')
parser.add_argument('-d', '--dry-run', dest='dryrun',
                    action='store_true', default=False,
                    help='Perform a dry-run')

# Parse arguments.
args = parser.parse_args()
location = args.location
dryrun = args.dryrun
local = args.local
projects = args.projects or next(os.walk(local))[1]
print(projects)
asdf

# Setup variables.
local = r"C:\Users\eko\Desktop\Northcote High School\8. Git\TEST"
remote = {
  #'work': r"Z:\Northcote High School\8. Git",
  'work': r"C:\Users\eko\Desktop\Northcote High School\8. Git\TEST-REMOTE",
  'home': r"C:\Users\eko\Desktop\VIRTUAL\home"
}
ffs = r"C:\Program Files\FreeFileSync\FreeFileSync.exe"

# Setup fetch flag info (to create a summary when pulling).
fetchFlags = [
  '[new tag]',
  '[new head]',
  '[head uptodate]',
  '[tag update]',
  '[rejected]',
  '[forced update]',
  '[fast forward]',
  '[error]'
]

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

  # Setup local repo to point to remote.
  try:
    localDest = localRepo.remote(location).set_url(remoteDir)
  except:
    localDest = localRepo.create_remote(location, remoteDir)

  # Setup tracking branches.
  print('Setting up local branches.', flush=True)
  for branch in remoteRepo.branches:
    branchStr = str(branch)
    try:
      localRepo.create_head(branchStr, branch).set_tracking_branch(branch)
      print('\t{:10}:\tAdded.'.format(branchStr))
    except:
      print('\t{:10}:\tAlready exists.'.format(branchStr))

  # Check if repo is dirty (uncommitted/untracked files).
  if localRepo.is_dirty(untracked_files=True):
    print('Local repo dirty - skipping.\n', flush=True)
    continue

  # Fetch from remote.
  print('Fetching local from remote.', flush=True)
  if dryrun:
    infoList = localDest.fetch(['refs/heads/*:refs/heads/*', 'refs/tags/*:refs/tags/*', '--update-head-ok', '--dry-run'])
  else:
    infoList = localDest.fetch(['refs/heads/*:refs/heads/*', 'refs/tags/*:refs/tags/*', '--update-head-ok'])
  for info in infoList:
    summary = [fetchFlags[i] for i in range(0,len(fetchFlags)) if info.flags & 2**i]
    summary = ' '.join(summary)
    print('\t{:10}:\t{}'.format(str(info.ref), summary))

  # Reset current branch (necessary if current branch was fetched to).
  print('Hard resetting {}.'.format(localRepo.head.ref))
  if not dryrun:
    localRepo.head.reset('--hard')

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
