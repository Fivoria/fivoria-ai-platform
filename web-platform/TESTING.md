# Fivoria AI Web Platform - Testing Guide

## Unit Tests

### Frontend Tests
```bash
cd frontend
npm test
```

### Backend Tests
```bash
cd services/web-api
pytest tests/
```

## Integration Tests

### API Integration
```bash
cd web-platform
pytest tests/integration/
```

## End-to-End Tests

### Manual Testing Checklist

#### Authentication
- [ ] User can register new account
- [ ] User can login with credentials
- [ ] JWT token is properly stored
- [ ] Invalid credentials are rejected
- [ ] Token refresh works correctly

#### Project Management
- [ ] User can create new project
- [ ] User can list all projects
- [ ] User can update project details
- [ ] User can delete project
- [ ] Project isolation works correctly

#### File Operations
- [ ] User can create files
- [ ] User can read files
- [ ] User can update files
- [ ] User can delete files
- [ ] File tree displays correctly
- [ ] Monaco editor works properly

#### AI Chat
- [ ] Chat interface loads
- [ ] User can send messages
- [ ] AI responses stream correctly
- [ ] Markdown renders properly
- [ ] Code blocks have syntax highlighting
- [ ] Tool calls are displayed
- [ ] Citations are shown

#### Terminal
- [ ] Terminal panel opens
- [ ] Commands execute correctly
- [ ] Output displays properly
- [ ] Commands are sandboxed
- [ ] Dangerous commands require approval

#### Preview
- [ ] Preview panel opens
- [ ] Preview loads correctly
- [ ] Viewport switching works
- [ ] Refresh works
- [ ] External link opens correctly

#### Git Integration
- [ ] Git panel shows history
- [ ] Branches display correctly
- [ ] Checkout works
- [ ] Commit works
- [ ] Push/pull works

#### Document Upload
- [ ] User can upload documents
- [ ] Upload progress shows
- [ ] Processing status updates
- [ ] Documents appear in knowledge base

#### Memory System
- [ ] Memory panel shows entries
- [ ] Filtering works
- [ ] Memory can be cleared
- [ ] Different memory types display

#### Tools
- [ ] Tools panel shows available tools
- [ ] Tools can be enabled/disabled
- [ ] Tool execution works
- [ ] Permission levels display

#### Agent Tasks
- [ ] Tasks panel shows active tasks
- [ ] Task progress updates
- [ ] Tasks can be cancelled
- [ ] Task results display

#### Verification
- [ ] Tests can be run
- [ ] Test results display
- [ ] Passed/failed status shows
- [ ] Test duration shows

## Performance Testing

### Load Testing
```bash
# Using k6
k6 run tests/load-test.js
```

### API Performance
- Target: < 100ms for API responses
- Target: < 500ms for AI responses
- Target: < 1s for file operations

## Security Testing

### Authentication
- Test JWT token expiration
- Test invalid token handling
- Test refresh token flow

### Authorization
- Test RBAC permissions
- Test project access control
- Test file access control

### Input Validation
- Test SQL injection prevention
- Test XSS prevention
- Test command injection prevention

## Browser Compatibility

Test on:
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Mobile Testing

Test on:
- iOS Safari
- Android Chrome
- Responsive design verification
