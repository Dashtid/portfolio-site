# David Dashti Portfolio

This repository contains the source code for [dashti.se](https://dashti.se), a personal portfolio and project hub focused on cybersecurity in healthcare.

## Project Overview

This is a static website (HTML, CSS, JS) deployed using [Azure Static Web Apps](https://docs.microsoft.com/en-us/azure/static-web-apps/). The site serves as a central hub for my resume, project links, and professional information, with a focus on quality assurance and cybersecurity in medical software.

## Directory Structure

```plaintext
site/
├── index.html
├── fdf.html
├── hermes.html
├── karolinska.html
├── market-analysis.html
├── philips.html
├── scania.html
├── sos.html
├── static/
│   ├── css/
│   │   └── style.css
│   ├── images/
│   └── js/
staticwebapp.config.json
README.md
```

- **index.html**: Main landing page with navigation to all sections.
- **fdf.html**: Finnish Defence Forces experience.
- **hermes.html**: Hermes Medical Solutions experience.
- **karolinska.html**: Karolinska University Hospital experience.
- **market-analysis.html**: Interactive dashboards and market analysis.
- **philips.html**: Philips Healthcare experience.
- **scania.html**: Scania Engines experience.
- **sos.html**: Södersjukhuset (SÖS) experience.
- **static/**: Contains all static assets (CSS, images, JS).
- **staticwebapp.config.json**: Azure Static Web Apps configuration file.

## Deployment

Deployment is fully automated:

- Any push to the `master` branch triggers a GitHub Actions workflow.
- The workflow deploys the contents of the `site/` directory to Azure Static Web Apps.
- The site is live at [agreeable-sky-0d52c1303.6.azurestaticapps.net](https://agreeable-sky-0d52c1303.6.azurestaticapps.net) and (once DNS is propagated) at [dashti.se](https://dashti.se).

### How to Update the Site

1. Edit or add files in the `site/` directory (e.g., `index.html`, `hermes.html`).
2. Commit and push your changes to the `master` branch.
3. GitHub Actions will automatically deploy your changes to Azure.

## Local Development

You can preview your site locally by opening `site/index.html` in your browser. No build step is required.

## License

MIT

---

\_Maintained by David Dashti. For questions or suggestions, please open an issue
