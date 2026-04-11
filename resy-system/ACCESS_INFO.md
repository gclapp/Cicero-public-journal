# Resy System - Access Information

## 🎉 Setup Complete!

Your Resy automation system is live with HTTPS!

---

## 📍 Access URLs

| URL | Description |
|-----|-------------|
| **https://nyceats.openclapp.com** | **✅ HTTPS (Recommended)** |
| http://nyceats.openclapp.com | HTTP (redirects to HTTPS) |
| http://16.59.79.163 | Direct IP (Elastic IP) |

---

## 🔐 Login Credentials

| Field | Value |
|-------|-------|
| **Username** | `admin` |
| **Password** | `yUMKRRj6cqXIq0maSIKa2Q==` |

Password also saved in: `/home/ubuntu/.openclaw/workspace/resy-system/.admin_password`

---

## 🛡️ Security Features

- ✅ **HTTPS/SSL** - Valid certificate (expires 2026-07-10)
- ✅ **Basic Authentication** - Password required
- ✅ **Firewall (UFW)** - Ports 22, 80, 443 only
- ✅ **Fail2Ban** - Blocks brute force attacks
- ✅ **Rate Limiting** - 10 req/sec per IP
- ✅ **Auto-renewal** - SSL renews automatically

---

## 📊 Service Status

```bash
./status.sh                    # Check all services
sudo systemctl status resy-system   # App status
sudo systemctl status nginx         # Web server status
```

---

## 🔄 Management Commands

```bash
# Restart services
sudo systemctl restart resy-system
sudo systemctl restart nginx

# View logs
sudo journalctl -u resy-system -f
tail -f logs/gunicorn-error.log
sudo tail -f /var/log/nginx/error.log

# Test health
curl https://nyceats.openclapp.com/health
```

---

## 📝 What's Running

| Service | Purpose |
|---------|---------|
| Gunicorn | Flask app server (localhost:5000) |
| Nginx | Reverse proxy, SSL, auth |
| Certbot | SSL auto-renewal |
| UFW | Firewall |
| Fail2Ban | Intrusion prevention |

---

## 🎯 Next Steps

1. **Visit:** https://nyceats.openclapp.com
2. **Login** with credentials above
3. **Add NYC restaurants** via web interface
4. **Set priorities** via drag-and-drop
5. **Share with Grace** if desired

---

**Setup completed:** April 11, 2026
**SSL Certificate:** Valid until July 10, 2026 (auto-renews)
**Elastic IP:** 16.59.79.163 (persistent)
