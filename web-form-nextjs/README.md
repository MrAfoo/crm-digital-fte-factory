# NovaDeskAI Web Support Form

A modern, production-ready Next.js web support form built with React 18, TypeScript, and Tailwind CSS. Features a glassmorphism design with animated backgrounds and comprehensive ticket management capabilities.

## Features

### Support Form
- **Full TypeScript Support**: Completely typed for safety and IDE autocomplete
- **Client-side Validation**: Real-time validation with detailed error messages
- **Form Fields**:
  - Full Name (2+ characters required)
  - Email (valid email format required)
  - Subject (3+ characters required)
  - Preferred Contact Channel (Web, Email, or WhatsApp)
  - Issue Description (10-1000 characters)
- **Character Counter**: Live character count for description field
- **Loading States**: Visual feedback during form submission
- **Success State**: Displays ticket ID (TKT-XXXX format) after successful submission
- **Error Handling**: Graceful error handling with retry functionality
- **Glassmorphism Design**: Modern dark theme with animated orbs
- **Responsive**: Fully responsive on mobile, tablet, and desktop

### Ticket Status Tracking
- **Search Functionality**: Look up tickets by ID
- **Ticket Details**: View status, priority, channel, and timestamps
- **Conversation History**: Full conversation thread with timestamps
- **Status Indicators**: Color-coded status badges
- **Priority Levels**: Visual priority indicators

### Design System
- **Color Scheme**:
  - Dark Background: `#0f0e17`
  - Primary: `#6C63FF`
  - Accent: `#f43f5e`
- **Animations**: Smooth transitions, animated background orbs, and fade-in effects
- **Dark Theme**: Complete dark mode implementation with accessible contrast

## Tech Stack

- **Framework**: Next.js 14
- **UI Library**: React 18
- **Language**: TypeScript 5.3
- **Styling**: Tailwind CSS 3.4
- **Package Manager**: npm

## Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

## Installation

1. **Clone the repository**:
   ```bash
   cd web-form-nextjs
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```

   The application will be available at `http://localhost:3000`

## Project Structure

```
web-form-nextjs/
├── app/
│   ├── layout.tsx              # Root layout with Inter font
│   ├── page.tsx                # Home page with support form
│   ├── globals.css             # Global styles and animations
│   └── ticket/
│       └── [id]/
│           └── page.tsx        # Dynamic ticket status page
├── components/
│   ├── SupportForm.tsx         # Main support form component
│   └── TicketStatus.tsx        # Ticket status lookup component
├── package.json                # Dependencies
├── next.config.js              # Next.js configuration
├── tsconfig.json               # TypeScript configuration
├── tailwind.config.js          # Tailwind CSS configuration
└── README.md                   # This file
```

## API Integration

### Create Support Ticket

**Endpoint**: `POST http://localhost:8000/api/tickets`

**Request Body**:
```json
{
  "fullName": "John Doe",
  "email": "john@example.com",
  "subject": "Cannot login to my account",
  "channel": "web",
  "description": "I'm unable to log in with my credentials..."
}
```

**Response**:
```json
{
  "success": true,
  "ticketId": "TKT-12345"
}
```

### Check Ticket Status

**Endpoint**: `GET http://localhost:8000/api/tickets/{ticketId}`

**Response**:
```json
{
  "id": "TKT-12345",
  "status": "open",
  "subject": "Cannot login to my account",
  "createdDate": "2024-01-15T10:30:00Z",
  "lastUpdated": "2024-01-15T14:45:00Z",
  "priority": "high",
  "channel": "web",
  "conversation": [
    {
      "id": "msg-1",
      "author": "Support Agent",
      "message": "Thank you for contacting us...",
      "timestamp": "2024-01-15T10:35:00Z"
    }
  ]
}
```

## Component Documentation

### SupportForm Component

The main form component for submitting support tickets.

**Props**: None

**State**:
- `formData`: User input data
- `errors`: Form validation errors
- `isLoading`: Loading state during submission
- `isSubmitted`: Success state flag
- `ticketId`: Returned ticket ID
- `submitError`: Error message
- `charCount`: Character counter for description

**Features**:
- Real-time validation with error clearing on input
- Max 1000 characters for description
- Loading spinner during submission
- Success state with ticket ID display
- Error state with retry button
- Responsive design with mobile optimization

### TicketStatus Component

Component for searching and viewing ticket details.

**Props**:
- `initialTicketId` (optional): Pre-fill the search field with a ticket ID

**State**:
- `ticket`: Loaded ticket data
- `isLoading`: Search loading state
- `error`: Search error message
- `hasSearched`: Whether a search has been performed

**Features**:
- Search by ticket ID
- Display ticket metadata (status, priority, channel, dates)
- Show conversation history
- Color-coded status and priority badges
- Date formatting

## Validation Rules

### Full Name
- Required field
- Minimum 2 characters
- Trimmed of whitespace

### Email
- Required field
- Must be valid email format
- Standard email validation regex

### Subject
- Required field
- Minimum 3 characters
- Trimmed of whitespace

### Description
- Required field
- Minimum 10 characters
- Maximum 1000 characters
- Character counter provided

## Styling and Customization

### Global Styles

Edit `app/globals.css` to customize:
- Base colors and fonts
- Glassmorphism effects
- Animation keyframes
- Scrollbar styling

### Theme Colors

Modify `tailwind.config.js` to change:
- `nova-dark`: Background color
- `nova-primary`: Primary accent color
- `nova-accent`: Secondary accent color
- `nova-light`: Light text color

### Animations

Available animations:
- `animate-float`: Floating orbs
- `animate-pulse-glow`: Pulsing glow effect
- `animate-slide-up`: Slide up entrance animation
- `spinner`: Loading spinner rotation

## Building for Production

1. **Build the application**:
   ```bash
   npm run build
   ```

2. **Start the production server**:
   ```bash
   npm start
   ```

## Environment Variables

Create a `.env.local` file if you need to configure the API endpoint:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Then update the components to use: `process.env.NEXT_PUBLIC_API_URL`

## Error Handling

The application includes comprehensive error handling:
- Network errors are caught and displayed
- Invalid responses are handled gracefully
- Validation errors are shown per field
- Retry functionality for failed submissions
- User-friendly error messages

## Performance Optimizations

- Code splitting and lazy loading via Next.js
- Optimized CSS with Tailwind
- Efficient state management with React hooks
- No external UI library bloat (pure Tailwind CSS)

## Accessibility

- Semantic HTML structure
- Proper label associations
- ARIA attributes where applicable
- Keyboard navigation support
- Color contrast compliance

## Browser Support

- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Troubleshooting

### Port 3000 Already in Use

```bash
# On macOS/Linux
lsof -i :3000
kill -9 <PID>

# Or use a different port
npm run dev -- -p 3001
```

### API Connection Errors

- Ensure the backend API is running on `http://localhost:8000`
- Check CORS settings in the backend
- Verify network connectivity
- Check browser console for detailed error messages

### Build Errors

```bash
# Clear Next.js cache
rm -rf .next

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Try building again
npm run build
```

## License

MIT

## Support

For issues or questions, please contact the NovaDeskAI team or create an issue in the repository.
