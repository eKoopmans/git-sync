### INSTRUCTIONS:
# 1. Add ~/bin to PATH
#   (~ is %USERPROFILE% in Windows)
# 2. Copy this and gitPull.cmd to ~/bin
# 3. Run from your desired Git folder:
#   gitPull [ARGUMENTS]

### TODO:
# - check if there's any updates to active branch before stashing/unstashing
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

# Setup variables.
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

# Loop through all dirs.
for project in projects:
  # Progress update.
  print(project + ':', flush=True)

  # Check if the remote is a git project.
  remoteDir = os.path.join(remote[location], project)
  try:
    remoteRepo = Repo(remoteDir)
  except:
    print('- Not a repo.\n', flush=True)
    continue

  # Setup the local dir if necessary.
  localDir = os.path.join(local, project)
  try:
    os.makedirs(localDir)
  except:
    pass

  # Setup the local repo if necessary.
  try:
    localRepo = Repo(localDir)
  except:
    localRepo = Repo.init(localDir)

  # Setup local repo to point to remote.
  try:
    localDest = localRepo.remote(location).set_url(remoteDir)
  except:
    localDest = localRepo.create_remote(location, remoteDir)

  # Setup tracking branches.
  print('- Setting up local branches.', flush=True)
  for branch in remoteRepo.branches:
    branchStr = str(branch)
    try:
      localRepo.create_head(branchStr, branch).set_tracking_branch(branch)
      print('\t{:10}:\tAdded.'.format(branchStr))
    except:
      print('\t{:10}:\tAlready exists.'.format(branchStr))

  # Check if repo is dirty (uncommitted/untracked files).
  localDirty = localRepo.is_dirty(untracked_files=True)
  if localDirty:
    localRepo.git.stash(['save', '--include-untracked'])
    print('- Local repo dirty - stashing files.', flush=True)

  # Fetch from remote.
  print('- Fetching local from remote.', flush=True)
  try:
    if dryrun:
      infoList = localDest.fetch(['refs/heads/*:refs/heads/*', 'refs/tags/*:refs/tags/*', '--update-head-ok', '--dry-run'])
    else:
      infoList = localDest.fetch(['refs/heads/*:refs/heads/*', 'refs/tags/*:refs/tags/*', '--update-head-ok'])
    for info in infoList:
      summary = [fetchFlags[i] for i in range(0,len(fetchFlags)) if info.flags & 2**i]
      summary = ' '.join(summary)
      print('\t{:10}:\t{}'.format(str(info.ref), summary))
  except:
    print('\tError fetching (local may have unpushed commits).')

  # Reset current branch (necessary if current branch was fetched to).
  print('- Hard resetting {}.'.format(localRepo.head.ref))
  if not dryrun:
    localRepo.head.reset('--hard')

  # Restore any stashed files (if the main branch was dirty).
  if localDirty:
    # Needs to checkout stash for the tracked files AND stash^3
    # (the third ancestor) for the untracked files.
    # Info: https://stackoverflow.com/a/55799386/4080966
    localRepo.git.checkout(['stash', '--', '.'])
    try:
      localRepo.git.checkout(['stash^3', '--', '.'])
    except:
      pass
    localRepo.git.stash('drop')

    # Then reset the head to unstage the changes (the checkout above auto-stages).
    localRepo.head.reset()
    print('- Stashed files restored.', flush=True)
    print('  *** Check ALL restored files for clashes. ***', flush=True)

  # Progress update.
  print('- {} done!\n'.format(project), flush=True)

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
