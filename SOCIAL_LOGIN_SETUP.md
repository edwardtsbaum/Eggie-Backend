# Social Login & Phone Authentication Setup

This guide explains how to set up Facebook, Google, and phone number authentication for your IVF mobile app backend.

## New Authentication Methods

Your backend now supports multiple authentication methods:

1. **Email/Password** (existing)
2. **Facebook Login** (new)
3. **Google Login** (new)
4. **Phone Number + SMS** (new)

## Environment Configuration

Add these variables to your `.env` file:

```bash
# Facebook OAuth Configuration
FACEBOOK_APP_ID=your_facebook_app_id
FACEBOOK_APP_SECRET=your_facebook_app_secret

# Google OAuth Configuration (iOS)
GOOGLE_CLIENT_ID=your_google_client_id
# Note: iOS Google Sign-In doesn't use Client Secret

# SMS Service Configuration (for phone authentication)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
```

## Setup Instructions

### 1. Facebook Login Setup

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create a new app or use existing one
3. Add Facebook Login product
4. Configure OAuth settings:
   - Valid OAuth Redirect URIs: `https://your-domain.com/auth/facebook/callback`
   - App Domains: `your-domain.com`
5. Copy App ID and App Secret to your `.env` file

### 2. Google Login Setup (iOS)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Sign-In API
4. Create OAuth 2.0 credentials:
   - **Application type**: iOS
   - **Bundle ID**: Your iOS app's bundle identifier
5. Download the `GoogleService-Info.plist` file
6. Copy only the **Client ID** to your `.env` file
   - **Note**: iOS Google Sign-In doesn't use Client Secret

### 3. SMS Service Setup (Twilio Example)

1. Sign up for [Twilio](https://www.twilio.com/)
2. Get Account SID and Auth Token from dashboard
3. Purchase a phone number for SMS
4. Add credentials to your `.env` file

## API Endpoints

### Facebook Login
```bash
POST /auth/facebook
Content-Type: application/json

{
  "access_token": "facebook_access_token_from_mobile_app"
}
```

### Google Login
```bash
POST /auth/google
Content-Type: application/json

{
  "id_token": "google_id_token_from_mobile_app"
}
```

### Phone Authentication

**Step 1: Request verification code**
```bash
POST /auth/phone/request
Content-Type: application/json

{
  "phone_number": "+1234567890"
}
```

**Step 2: Verify code and get token**
```bash
POST /auth/phone/verify
Content-Type: application/json

{
  "phone_number": "+1234567890",
  "verification_code": "123456"
}
```

## Mobile App Integration

### Facebook Login (React Native Example)
```javascript
import { LoginManager, AccessToken } from 'react-native-fbsdk-next';

const facebookLogin = async () => {
  try {
    const result = await LoginManager.logInWithPermissions(['public_profile', 'email']);
    
    if (result.isCancelled) {
      console.log('Login cancelled');
      return;
    }
    
    const data = await AccessToken.getCurrentAccessToken();
    if (!data) {
      console.log('Something went wrong obtaining access token');
      return;
    }
    
    // Send to your backend
    const response = await fetch('https://your-api.com/auth/facebook', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        access_token: data.accessToken
      })
    });
    
    const { access_token } = await response.json();
    // Store token in your app
  } catch (error) {
    console.error('Facebook login error:', error);
  }
};
```

### Google Login (React Native iOS Example)
```javascript
import { GoogleSignin } from '@react-native-google-signin/google-signin';

const googleLogin = async () => {
  try {
    // Configure Google Sign-In (iOS)
    GoogleSignin.configure({
      iosClientId: 'your-ios-client-id', // From GoogleService-Info.plist
      // No webClientId needed for iOS-only apps
    });
    
    await GoogleSignin.hasPlayServices();
    const userInfo = await GoogleSignin.signIn();
    
    // Send to your backend
    const response = await fetch('https://your-api.com/auth/google', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        id_token: userInfo.idToken
      })
    });
    
    const { access_token } = await response.json();
    // Store token in your app
  } catch (error) {
    console.error('Google login error:', error);
  }
};
```

### Phone Authentication (React Native Example)
```javascript
const phoneLogin = async (phoneNumber) => {
  try {
    // Step 1: Request verification code
    const response = await fetch('https://your-api.com/auth/phone/request', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        phone_number: phoneNumber
      })
    });
    
    // Step 2: User enters code (you'll need to implement UI for this)
    const verificationCode = '123456'; // Get from user input
    
    // Step 3: Verify code
    const verifyResponse = await fetch('https://your-api.com/auth/phone/verify', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        phone_number: phoneNumber,
        verification_code: verificationCode
      })
    });
    
    const { access_token } = await verifyResponse.json();
    // Store token in your app
  } catch (error) {
    console.error('Phone login error:', error);
  }
};
```

## iOS-Specific Setup

### Google Sign-In for iOS

1. **Install the SDK**:
   ```bash
   npm install @react-native-google-signin/google-signin
   ```

2. **Add to iOS project**:
   ```bash
   cd ios && pod install
   ```

3. **Configure in your app**:
   ```javascript
   import { GoogleSignin } from '@react-native-google-signin/google-signin';
   
   // In your app initialization
   GoogleSignin.configure({
     iosClientId: 'your-ios-client-id', // From GoogleService-Info.plist
   });
   ```

4. **Backend Configuration**:
   - Only need `GOOGLE_CLIENT_ID` in your `.env` file
   - No `GOOGLE_CLIENT_SECRET` needed for iOS

## Security Considerations

1. **Token Validation**: Always verify tokens with the respective providers
2. **HTTPS**: Use HTTPS in production for all authentication endpoints
3. **Rate Limiting**: Implement rate limiting for phone verification requests
4. **Token Storage**: Store JWT tokens securely in mobile app
5. **User Privacy**: Only collect necessary user information

## Testing

### Demo Mode
For testing, the phone authentication uses a fixed verification code: `123456`

### Test Endpoints
```bash
# Test Facebook login (you'll need a real Facebook token)
curl -X POST "http://localhost:8000/auth/facebook" \
  -H "Content-Type: application/json" \
  -d '{"access_token": "your_facebook_token"}'

# Test phone authentication
curl -X POST "http://localhost:8000/auth/phone/request" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890"}'

curl -X POST "http://localhost:8000/auth/phone/verify" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890", "verification_code": "123456"}'
```

## Production Checklist

- [ ] Set up proper SMS service (Twilio, AWS SNS, etc.)
- [ ] Configure Facebook and Google OAuth apps for production
- [ ] Implement proper error handling and logging
- [ ] Set up monitoring for authentication failures
- [ ] Implement token refresh mechanism
- [ ] Add rate limiting for all auth endpoints
- [ ] Set up proper CORS configuration for your mobile app domains 