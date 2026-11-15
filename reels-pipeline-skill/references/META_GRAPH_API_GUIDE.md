# Meta Instagram Graph API Setup Guide

To enable automated posting to Instagram Reels via Meta's official API, follow these official onboarding steps.

---

## 1. Account Prerequisites
1. **Instagram Account**: Convert your personal Instagram account into a **Professional Account** (Creator or Business).
2. **Facebook Page**: Create a Facebook Page (or use an existing one) and link it to your Instagram Professional Account via **Instagram Settings &rarr; Business &rarr; Connect Facebook Page**.

---

## 2. Meta for Developers App Setup
1. Log in to [Meta for Developers](https://developers.facebook.com/).
2. Click **Create App** and select **Business** as the app type.
3. Name your app (e.g. `ReelsAutomationEngine`).
4. In the app dashboard, add the **Instagram Graph API** product.

---

## 3. Required Permissions
In the **Graph API Explorer** or App Permissions dashboard, request the following permissions:
- `instagram_basic`
- `instagram_content_publish`
- `pages_show_list`
- `pages_read_engagement`
- `business_management` (optional for Business Managers)

---

## 4. Generating a 60-Day Long-Lived Token
1. In the **Graph API Explorer**, select your app, choose **User Token**, and select the permissions above.
2. Click **Generate Access Token**.
3. Copy the short-lived token and exchange it for a long-lived (60-day) token:
```bash
curl -X GET "https://graph.facebook.com/v19.0/oauth/access_token?\
grant_type=fb_exchange_token&\
client_id=YOUR_META_APP_ID&\
client_secret=YOUR_META_APP_SECRET&\
fb_exchange_token=SHORT_LIVED_TOKEN"
```
4. Save the returned `access_token` into `.env` as `META_USER_ACCESS_TOKEN`.

---

## 5. Finding Your Instagram Account ID
Run the following query with your access token to retrieve your Instagram Business Account ID:
```bash
curl -X GET "https://graph.facebook.com/v19.0/me/accounts?access_token=YOUR_META_USER_ACCESS_TOKEN"
```
Find the linked Instagram account ID (`instagram_business_account.id`) and set it in `.env` as `INSTAGRAM_ACCOUNT_ID`.

---

## 6. How Publishing Works Under the Hood
1. **Container Creation**: `POST https://graph.facebook.com/v19.0/{ig_id}/media` with `media_type=REELS` and `video_url`.
2. **Status Polling**: `GET https://graph.facebook.com/v19.0/{container_id}?fields=status_code` until `status_code == FINISHED`.
3. **Publication**: `POST https://graph.facebook.com/v19.0/{ig_id}/media_publish` with `creation_id`.
4. **Permalink Extraction**: `GET https://graph.facebook.com/v19.0/{media_id}?fields=permalink`.
