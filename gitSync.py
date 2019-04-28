### INSTRUCTIONS:
# 1. Add ~/bin to PATH
#   (~ is %USERPROFILE% in Windows)
# 2. Copy this, gitSync.cmd, and template.ffs_batch to ~/bin
# 3. Run from your desired Git folder:
#   gitSync [ARGUMENTS]

### TODO:
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
from functools import partial

# Helper functions.
def uniqMerge(a,b):
  return sorted(set(a).union(b))
def listStr(data):
  return [str(x) for x in data]
def branchPrint(branchName, text):
  print('\t{:10}:\t{}'.format(branchName, text), flush=True)

# Function to stash/unstash before modifying active branch.
def stashRun(toRun, repo, branchName, location):
  # If branch is not the active branch, just run the function.
  if repo.active_branch.name != branchName:
    return toRun()

  # Check if repo is dirty (uncommitted/untracked files).
  isDirty = repo.is_dirty(untracked_files=True)
  if isDirty:
    if not dryrun:
      localRepo.git.stash(['save', '--include-untracked'])
    branchPrint(branchName, 'Stashing files ({} dirty).'.format(location))

  # Run the function.
  toRun()

  # Restore any stashed files (if the main branch was dirty).
  if isDirty:
    if not dryrun:
      # Needs to checkout stash AND stash^3 for tracked and untracked files.
      # Info: https://stackoverflow.com/a/55799386/4080966
      localRepo.git.checkout(['stash', '--', '.'])
      try:
        localRepo.git.checkout(['stash^3', '--', '.'])
      except:
        pass
      localRepo.git.stash('drop')

      # Then reset the head to unstage the changes (the checkout above auto-stages).
      localRepo.head.reset()

    # Progress update.
    branchPrint(branchName, 'Stash restored.')
    branchPrint(branchName, '*IMPORTANT:* Check all restored files for clashes.')

# Pull function.
def gitPull(localDest, branchName, dryrun):
  # Pull from remote.
  try:
    if dryrun:
      localDest.pull([branchName, '--dry-run'])
    else:
      localDest.pull([branchName])
    branchPrint(branchName, 'Pulled from remote.')
  except:
    branchPrint(branchName, 'Error pulling.')

# Push function.
def gitPush(localDest, branchName, dryrun):
  # Push to remote.
  try:
    if dryrun:
      localDest.push([branchName, '--follow-tags', '--dry-run'])
    else:
      localDest.push([branchName, '--follow-tags'])
    branchPrint(branchName, 'Pushed to remote.')
  except:
    branchPrint(branchName, 'Error pushing.')

# Setup command-line arguments.
parser = ArgumentParser(description='Pull all specified Git projects from a remote location.')
parser.add_argument('projects', metavar='PROJECT', nargs='*',
                    help='The names of each project to run (default: * in local)')
parser.add_argument('-t', '--target', dest='target', metavar='TARGET', default='local',
                    help='The name of the target remote location (default: local)')
parser.add_argument('-l', '--local', dest='local', metavar='LOCAL', default='.',
                    help='The local root of the projects (default: current dir)')
parser.add_argument('-r', '--remote', dest='remote', metavar='REMOTE', default='.',
                    help='The remote root of the projects (default: current dir)')
parser.add_argument('-d', '--dry-run', dest='dryrun', default=False,
                    action='store_true', help='Perform a dry-run')

# Parse arguments.
args = parser.parse_args()
projects = args.projects
target = args.target
local = args.local
remote = args.remote
dryrun = args.dryrun

# Setup variables.
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

# Gather projects if not explicitly set.
if not projects:
  projects = uniqMerge(next(os.walk(local))[1], next(os.walk(remote))[1])

# Fix if inside a git repo.
if '.git' in projects:
  projects = [os.getcwd().split(os.sep)[-1]]
  local = os.path.abspath(os.path.join(os.getcwd(), os.pardir))

# Loop through all dirs.
for project in projects:
  # Progress update.
  print(project + ':', flush=True)

  # Check if local is a git project.
  localDir = os.path.join(local, project)
  try:
    localRepo = Repo(localDir)
    localError = False
  except:
    localError = True

  # Check if remote is a git project.
  remoteDir = os.path.join(remote, project)
  try:
    remoteRepo = Repo(remoteDir)
    remoteError = False
  except:
    remoteError = True

  # Skip if neither is a git project.
  if localError and remoteError:
    print('- Not a repo.\n', flush=True)
    continue

  # Create local repo if necessary.
  if localError:
    try:
      os.makedirs(localDir)
      print('- Created local dir {}.'.format(localDir), flush=True)
    except:
      pass
    localRepo = Repo.init(localDir)
    print('- Initialised local repo.', flush=True)

  # Create remote repo if necessary.
  if remoteError:
    try:
      os.makedirs(remoteDir)
      print('- Created remote dir {}.'.format(remoteDir), flush=True)
    except:
      pass
    remoteRepo = Repo.init(remoteDir)
    print('- Initialised remote repo.', flush=True)

  # Setup local repo to point to remote.
  try:
    localDest = localRepo.remote(target).set_url(remoteDir)
  except:
    localDest = localRepo.create_remote(target, remoteDir)
    print('- Created new remote {} in local repo.'.format(target), flush=True)

  # Get full list of branches.
  localBranches = localRepo.branches
  remoteBranches = remoteRepo.branches
  branchNames = uniqMerge(listStr(localBranches), listStr(remoteBranches))

  # Sync each branch.
  print('- Syncing branches.', flush=True)
  for branchName in branchNames:
    # Setup local branch if necessary.
    if not branchName in localBranches:
      remoteBranch = remoteBranches[branchName]
      localRepo.create_head(branchName, remoteBranch).set_tracking_branch(remoteBranch)
      branchPrint(branchName, 'Created in local.')
    localBranch = localBranches[branchName]

    # Setup remote branch if necessary.
    if not branchName in remoteBranches:
      localBranch = localBranches[branchName]
      remoteRepo.create_head(branchName, localBranch)
      branchPrint(branchName, 'Created in remote.')
    remoteBranch = remoteBranches[branchName]

    # Sync the repos (push, pull, or neither).
    if localBranch.commit == remoteBranch.commit:
      branchPrint(branchName, 'Up to date.')
    else:
      mergeBase = localRepo.merge_base(localBranch, remoteBranch)[0]
      if mergeBase == localBranch.commit:
        stashRun(partial(gitPull, localDest, branchName, dryrun), localRepo, branchName, 'local')
      elif mergeBase == remoteBranch.commit:
        stashRun(partial(gitPush, localDest, branchName, dryrun), remoteRepo, branchName, target)
      else:
        branchPrint(branchName, 'Error - branches are diverged.')

  # Progress update.
  print('- {} done!\n'.format(project), flush=True)

# Synchronise all .devel folders with FreeFileSync (FFS).
print('Syncing all .devel folders.', flush=True)
if not dryrun:
  # Setup paths.
  ffsDevel = os.path.join(local, '{}Devel.ffs_batch'.format(target))

  # Create the FFS sync file if it doesn't exist.
  if not os.path.exists(ffsDevel):
    shutil.copy2(os.path.join(os.environ['USERPROFILE'], 'bin', 'template.ffs_batch'), ffsDevel)
    with fileinput.FileInput(ffsDevel, inplace=True) as file:
      for line in file:
        print(line.replace('%LOCAL%', local).replace('%REMOTE%', remote), end='')

  # Run the sync.
  subprocess.call([ffs, ffsDevel])

# Progress update.
print('Sync complete!', flush=True)
