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
from functools import partial

# Helper functions.
def uniqMerge(a,b):
  return sorted(set(a).union(b))
def listStr(data):
  return [str(x) for x in data]

# Function to stash/unstash before modifying active branch.
def stashRun(toRun, repo, branchName, location):
  # If branch is not the active branch, just run the function.
  if repo.active_branch.name != branchName:
    return toRun()

  # Check if repo is dirty (uncommitted/untracked files).
  isDirty = repo.is_dirty(untracked_files=True)
  if isDirty:
    localRepo.git.stash(['save', '--include-untracked'])
    print('- {} repo dirty - stashing files.'.format(location.title), flush=True)

  # Run the function.
  toRun()

  # Restore any stashed files (if the main branch was dirty).
  if isDirty:
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

# Pull function.
def gitPull(localDest, branchName, dryrun):
  # Pull from remote.
  print('- Pulling {}.'.format(branchName), flush=True)
  try:
    if dryrun:
      infoList = localDest.pull([branchName, '--dry-run'])
    else:
      infoList = localDest.fetch([branchName, '--update-head-ok'])
    for info in infoList:
      summary = [fetchFlags[i] for i in range(0,len(fetchFlags)) if info.flags & 2**i]
      summary = ' '.join(summary)
      print('\t{:10}:\t{}'.format(str(info.ref), summary))
  except:
    print('\tError fetching (local may have unpushed commits).')

# Push function.
def gitPush(localDest, branchName, dryrun):
  # Push to remote.
  print('- Pushing {}.'.format(branchName), flush=True)
  if dryrun:
    infoList = localDest.push([branchName, '--follow-tags', '--dry-run'])
  else:
    infoList = localDest.push([branchName, '--follow-tags'])
  for info in infoList:
    print('\t{:10}:\t{}'.format(str(info.local_ref), info.summary.strip('\r\n')), flush=True)

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
projects = args.projects

# Setup variables.
if location == 'work':
  remote = r"C:\Users\eko\Desktop\Northcote High School\8. Git\TEST-REMOTE"
else:
  remote = r"C:\Users\eko\Desktop\VIRTUAL\home"
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
    localDest = localRepo.remote(location).set_url(remoteDir)
  except:
    localDest = localRepo.create_remote(location, remoteDir)
    print('- Created new remote {} in local repo.'.format(location), flush=True)

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
      print('\t{:10}:\tAdded to local.'.format(branchName), flush=True)
    localBranch = localBranches[branchName]

    # Setup remote branch if necessary.
    if not branchName in remoteBranches:
      localBranch = localBranches[branchName]
      remoteRepo.create_head(branchName, localBranch)
      print('\t{:10}:\tAdded to remote.'.format(branchName), flush=True)
    remoteBranch = remoteBranches[branchName]

    # Sync the repos (push, pull, or neither).
    if localBranch.commit == remoteBranch.commit:
      print('\t{:10}:\tUp to date.'.format(branchName), flush=True)
    else:
      mergeBase = localRepo.merge_base(localBranch, remoteBranch)[0]
      if mergeBase == localBranch.commit:
        stashRun(partial(gitPull, localDest, branchName, dryrun), localRepo, branchName, 'local')
        print('\t{:10}:\tPulled from remote.'.format(branchName), flush=True)
      elif mergeBase == remoteBranch.commit:
        stashRun(partial(gitPush, localDest, branchName, dryrun), remoteRepo, branchName, location)
        print('\t{:10}:\tPushed to remote.'.format(branchName), flush=True)
      else:
        print('\t{:10}:\tError - branches are diverged.'.format(branchName), flush=True)

  # Progress update.
  print('- {} done!\n'.format(project), flush=True)

# Synchronise all .devel folders with FreeFileSync (FFS).
localDevel = os.path.join(localDir, '.devel')
if not dryrun and os.path.isdir(localDevel):
  # Setup paths.
  print('Syncing all .devel folders.', flush=True)
  ffsDevel = os.path.join(remote, 'gitDevel.ffs_batch')

  # Create the FFS sync file if it doesn't exist.
  if not os.path.exists(ffsDevel):
    shutil.copy2('./template.ffs_batch', ffsDevel)
    with fileinput.FileInput(ffsDevel, inplace=True) as file:
      for line in file:
        print(line.replace('%LOCAL%', local).replace('%REMOTE%', remote), end='')

  # Run the sync.
  subprocess.call([ffs, ffsDevel])

# Progress update.
print('All done!', flush=True)
