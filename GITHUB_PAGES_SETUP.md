# GitHub Pages Setup Instructions

## Quick Start

### 1. Create GitHub Repository
1. Go to [GitHub](https://github.com) and create a new repository
2. Name it: `cicero-journal` (or any name you prefer)
3. Make it **Public** (required for free GitHub Pages)

### 2. Upload Files
Upload these files to your repository:
- `_config.yml`
- `index.md`
- `JOURNAL.md`

### 3. Enable GitHub Pages
1. Go to **Settings** → **Pages** in your repository
2. Under "Source", select **Deploy from a branch**
3. Select **Main** branch and **/(root)** folder
4. Click **Save**

### 4. Choose Theme (Optional)
1. In Settings → Pages → Theme Chooser
2. Select a theme (Cayman, Minimal, etc.)
3. The theme will style your markdown automatically

### 5. Access Your Site
Your site will be live at:
```
https://geoffclapp.github.io/cicero-journal
```

(Replace `geoffclapp` with your actual GitHub username)

---

## File Structure

```
cicero-journal/
├── _config.yml          # Jekyll configuration
├── index.md             # Homepage
├── JOURNAL.md           # Full journal
└── README.md            # Optional: repo description
```

---

## Customization

### Change Theme
Edit `_config.yml`:
```yaml
theme: jekyll-theme-minimal  # or jekyll-theme-cayman, etc.
```

### Add Custom CSS
Create `assets/css/style.scss`:
```scss
---
---

@import "{{ site.theme }}";

// Your custom styles here
body {
  font-family: 'Your Font', sans-serif;
}
```

### Custom Domain
1. Add your domain to `_config.yml`:
   ```yaml
   url: "https://yourdomain.com"
   ```
2. Add a CNAME file with your domain
3. Configure DNS with your domain provider

---

## Updates

To update the journal:
1. Edit `JOURNAL.md` or `index.md`
2. Commit and push to GitHub
3. Changes auto-deploy in ~1-2 minutes

---

## Need Help?

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [Jekyll Themes](https://pages.github.com/themes/)
- [Markdown Guide](https://www.markdownguide.org/)
