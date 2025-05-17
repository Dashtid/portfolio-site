
<pre><div data-gramm="false" class=" relative bg-neutral-100 dark:bg-neutral-800 mb-2 "><div class=" px-[15px] py-[10px] rounded-b-[4px] border-[1px] border-t-0 border-[rgba(128,128,128,0.4)] "># David Dashti Portfolio  
  
This repository contains the source code for [daviddashti.com](https://daviddashti.com), a personal portfolio and project hub focused on cybersecurity in healthcare.  
  
## Project Overview  
  
This is a static website (HTML, CSS, JS) deployed using [Azure Static Web Apps](https://docs.microsoft.com/en-us/azure/static-web-apps/). The site serves as a central hub for my resume, project links, and professional information.  
  
## Directory Structure  
  
</div></div></pre>

.

├── .github/

│   ├── site/

│   │   ├── index.html

│   │   ├── projects.html

│   │   └── static/

│   │       ├── css/

│   │       ├── js/

│   │       └── images/

│   └── workflows/

│       └── azure-static-web-apps.yml

├── .gitignore

├── README.md

└── staticwebapp.config.json

```
  
- **.github/site/**: All static website content (HTML, CSS, JS, images)  
- **.github/workflows/azure-static-web-apps.yml**: GitHub Actions workflow for automated deployment to Azure  
- **staticwebapp.config.json**: Azure Static Web Apps configuration (routes, rewrites, etc.)  
- **.gitignore**: Files and folders excluded from version control  
  
## Deployment  
  
Deployment is fully automated:  
- Any push to the `master` branch triggers a GitHub Actions workflow.  
- The workflow deploys the contents of `.github/site/` to Azure Static Web Apps.  
- The site is live at [your Azure Static Web App URL](https://agreeable-sky-0d52c1303.6.azurestaticapps.net) (or your custom domain).  
  
### How to Update the Site  
  
1. Edit or add files in `.github/site/` (e.g., `index.html`).  
2. Commit and push your changes to the `master` branch.  
3. GitHub Actions will automatically deploy your changes to Azure.  
  
## Local Development  
  
You can preview your site locally by opening `.github/site/index.html` in your browser. No build step is required.  
  
## License  
  
MIT  
  
---  
  
*Maintained by David Dashti. For questions or suggestions, please open an issue or contact me directly.*  
```
