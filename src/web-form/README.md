# NovaDeskAI Web Form

A modern, self-contained HTML support form for customer success workflows.

## Quick Start

### Standalone Usage

Simply open `index.html` in your web browser:

```bash
# No build or server required - works standalone!
open src/web-form/index.html
```

Or serve it locally:

```bash
python -m http.server 8080
# Then visit http://localhost:8080/src/web-form/index.html
```

### Using with the API

To enable ticket submission functionality, ensure the NovaDeskAI API is running:

```bash
cd src/api
pip install fastapi uvicorn pydantic email-validator
python main.py
```

The API will start on `http://localhost:8000`. The form automatically targets this endpoint at `POST /api/tickets`.

## Embedding in an iframe

To embed the form in another website:

```html
<iframe 
  src="http://localhost:8000/web-form/" 
  width="600" 
  height="900" 
  frameborder="0"
  style="border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
</iframe>
```

Or embed it directly in your HTML (copy the entire `index.html` content).

## Configuration

### Changing the API Endpoint

Edit the `API_ENDPOINT` variable in the `<script>` section:

```javascript
const API_ENDPOINT = 'http://your-api-domain.com/api/tickets';
```

### Styling & Branding

The form uses CSS custom properties and inline styles. You can customize:

- **Primary Color**: Change `#6C63FF` (purple) throughout the CSS
- **Secondary Color**: Change `#FF6584` (pink) for accents
- **Font**: Modify the `font-family` property (currently Inter from Google Fonts)
- **Logo & Tagline**: Edit the `.logo` and `.tagline` HTML elements

## Features

- ✅ **Real-time Validation**: Fields validate as you type with helpful error messages
- ✅ **Character Counter**: Description field shows remaining characters (max 1000)
- ✅ **Loading States**: Spinner animation during submission
- ✅ **Success Confirmation**: Shows generated ticket number (TKT-XXXX)
- ✅ **Error Handling**: Network errors display friendly message with retry option
- ✅ **Responsive Design**: Works beautifully on mobile and desktop
- ✅ **Accessibility**: ARIA labels, keyboard navigation, focus states
- ✅ **iframe Communication**: Posts success/error events to parent window
- ✅ **No External Dependencies**: All CSS and JavaScript inline except Google Fonts

## Validation Rules

| Field | Rules |
|-------|-------|
| Full Name | Required, non-empty |
| Email | Required, valid email format |
| Subject | Required, non-empty |
| Channel | Required, must be Web/Email/WhatsApp |
| Description | Required, 20-1000 characters |

## API Response Format

On successful submission, the API returns:

```json
{
  "ticket_id": "TKT-1234",
  "status": "open",
  "message": "Your support ticket has been created successfully.",
  "estimated_response_time": "< 2 minutes",
  "created_at": "2024-01-15T10:30:00.000Z"
}
```

## iframe Message Events

The form sends postMessage events to the parent window:

### Success Event
```javascript
window.addEventListener('message', (event) => {
  if (event.data.type === 'ticket_submitted') {
    console.log('Ticket ID:', event.data.ticket_id);
    console.log('Submitted at:', event.data.timestamp);
  }
});
```

### Error Event
```javascript
window.addEventListener('message', (event) => {
  if (event.data.type === 'ticket_error') {
    console.log('Error:', event.data.message);
  }
});
```

### Reset the Form
```javascript
const iframe = document.querySelector('iframe');
iframe.contentWindow.postMessage({ action: 'reset' }, '*');
```

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Troubleshooting

### "Failed to fetch" Error
Ensure the API is running on `http://localhost:8000`. Check CORS is properly configured on the backend.

### Form won't submit
- Verify all required fields are filled
- Check browser console for validation errors
- Ensure the API endpoint is correct

### Styling looks different
The form loads the Inter font from Google Fonts. If you have no internet connection, it will fall back to system fonts (still functional, just different appearance).

## Development

To modify the form:

1. Edit `index.html` directly
2. Reload your browser
3. No build step required

All CSS and JavaScript are inline for maximum portability and self-containment.
