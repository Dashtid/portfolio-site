# David Dashti Portfolio

This repository contains the source code for [daviddashti.se](https://daviddashti.se), a personal portfolio and project hub focused on cybersecurity in healthcare.

## Project Overview

This is a static website (HTML, CSS, JS) deployed using [Azure Static Web Apps](https://docs.microsoft.com/en-us/azure/static-web-apps/). The site serves as a central hub for my resume, project links, and professional information, with a focus on quality assurance and cybersecurity in medical software.

## Directory Structure

.
├── .github/
│ └── workflows/
│ └── azure-static-web-apps.yml
├── site/
│ ├── index.html
│ ├── projects.html
│ └── static/
│ ├── css/
│ ├── js/
│ └── images/
├── .gitignore
├── README.md
└── staticwebapp.config.json

- **.github/workflows/**: Contains the Azure Static Web Apps workflow configuration.
- **site/**: Contains all static website content (HTML, CSS, JS, images).
- **.gitignore**: Specifies intentionally untracked files that Git should ignore.
- **staticwebapp.config.json**: Configuration file for Azure Static Web Apps, defining routes, rewrites, and other settings.

## Deployment

Deployment is fully automated:

- Any push to the `master` branch triggers a GitHub Actions workflow.
- The workflow deploys the contents of the `site/` directory to Azure Static Web Apps.
- The site is live at [agreeable-sky-0d52c1303.6.azurestaticapps.net](https://agreeable-sky-0d52c1303.6.azurestaticapps.net) and (once DNS is propagated) at [daviddashti.se](https://daviddashti.se).

### How to Update the Site

1. Edit or add files in the `site/` directory (e.g., `index.html`).
2. Commit and push your changes to the `master` branch.
3. GitHub Actions will automatically deploy your changes to Azure.

## Local Development

You can preview your site locally by opening `site/index.html` in your browser. No build step is required.

## License

MIT

---

*Maintained by David Dashti. For questions or suggestions, please open an issue or contact me directly.*
