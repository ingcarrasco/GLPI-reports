##### …or create a new repository on the command line
```sh
echo "# GLPI-reports" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/ingcarrasco/GLPI-reports.git
git push -u origin main
```

##### …or push an existing repository from the command line

```sh
git remote add origin https://github.com/ingcarrasco/GLPI-reports.git
git branch -M main
git push -u origin main
```