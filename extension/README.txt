This folder structure accommodates differences between different browsers,
while keeping most files identical.

New version development workflow:
---------------------------------

1. update the new version numbers in manifest.json of each browser subdir;
    make sure they are all identical (this could be automated, as an argument
    to the build script, with a placeholder replacement in each manifest file)

1a. add update wording in popup.js

2. run build.bat (might be python if enhancement is needed in the future)
    to create extension .zip files

3. remove the production extension from each browser

4. unzip the .zip files

5. in Manage Extensions, use Load Unpacked to load the unzipped chrome dir

6. make sure the host manifest.json allows the sideloaded id

7. hack on the files in the unzipped chrome dir; reload (from Manage Extensions
    page) as needed - note that popup.* are reloaded every time you open the
    popup, so extension reload is only needed for edits to background.js etc

8. when happy, copy those files back to the extension/common dir

9. rebuild

10. unzip and temporarily load the extension, in all browsers, to confirm behavior
    (in Firefox, this is not the same as 'Load extension from file' - go to
     about:debugging#/runtime/this-firefox and select 'Load Temporary Add-on...';
     select the .zip file)

11. delete the unzipped directories (above) so they don't get committed to github, then
     commit all the updates, always including a new host version with matching version#,
     even if no functional changes were made to the host - since users will see a host
     update notice after the extension is updated since the version numbers are different
     until the host is updated

12. when ready to publish, send new .zip files to various web stores
files ready to be sent to Chrome Web Store and AMO (addons.mozilla.org).

