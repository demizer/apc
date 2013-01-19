# def add_package_to_repo(self, package, arch):
    # '''Adds a package to a repository set in the config.

    # :package: The package to add.
    # :arch: The architecture to target.

    # '''
    # # Delete the old packages
    # repo = self.repo_path
    # old_pkgs = glob.glob(os.path.join(repo, arch, package + '*'))
    # for pkg in old_pkgs:
        # log('Deleting old repo package ' + pkg)
        # try:
            # os.remove(pkg)
        # except:
            # logr.warning('Error: could not remove package')

    # # Copy the packages in stage to to the repo
    # ppath = os.path.join(self.base_path, 'stage', package)
    # log('Copying "{}" to "{}"'.format(package, repo))
    # cp_pat = 'cp {0}*/* {2}/{1}/'
    # if run(cp_pat.format(ppath, arch, repo), True) > 1:
        # logr.critical('Error: could not move the package to the repo')
        # sys.exit(1)

    # # Copy the package source in stage to the repo directory
    # ppath = os.path.join(self.base_path, 'stage', package)
    # if run('cp {0}*/*.src.tar.gz {1}/'.format(ppath, repo), True) > 1:
        # logr.warning('Error: could not move the package source to the '
                        # 'repo')

    # # Add the new packages to the repo
    # repo_name = os.path.basename(os.getcwd())
    # pkg = glob.glob(package + '*.pkg.tar.xz')[0]
    # log('Adding "{}" to the "{}" {} repository.'.format(pkg, repo_name,
                                                        # arch))
    # repo_cmd = ['repo-add', '-s', '-v', '-k', self.signing_key, repo_name
    # +
                # '.db.tar.xz', pkg]
    # if run_in_path(os.path.join(repo, arch), repo_cmd) > 0:
        # logr.critical('Error: could not add the package to the repo')
        # sys.exit(1)
