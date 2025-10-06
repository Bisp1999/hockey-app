import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../../utils/api';
import './TenantRegistration.css';

interface ValidationErrors {
  organization_name?: string;
  subdomain?: string;
  admin_email?: string;
  admin_password?: string;
  admin_first_name?: string;
  admin_last_name?: string;
}

const TenantRegistration: React.FC = () => {
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    organization_name: '',
    subdomain: '',
    admin_email: '',
    admin_password: '',
    admin_confirm_password: '',
    admin_first_name: '',
    admin_last_name: '',
  });
  
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [subdomainSuggestions, setSubdomainSuggestions] = useState<string[]>([]);
  const [checking, setChecking] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear error for this field
    if (errors[name as keyof ValidationErrors]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const checkAvailability = async () => {
    if (!formData.organization_name && !formData.subdomain) return;
    
    setChecking(true);
    try {
      const response = await apiClient.post('/onboarding/check-availability', {
        organization_name: formData.organization_name,
        preferred_subdomain: formData.subdomain,
      });
      
      const newErrors: ValidationErrors = {};
      
      if (!response.data.organization_name.available) {
        newErrors.organization_name = response.data.organization_name.message;
      }
      
      if (!response.data.subdomain.available) {
        newErrors.subdomain = response.data.subdomain.message;
        if (response.data.subdomain.suggestions) {
          setSubdomainSuggestions(response.data.subdomain.suggestions);
        }
      } else {
        setSubdomainSuggestions([]);
      }
      
      setErrors(newErrors);
    } catch (error) {
      console.error('Error checking availability:', error);
    } finally {
      setChecking(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Client-side validation
    const newErrors: ValidationErrors = {};
    
    if (!formData.organization_name) {
      newErrors.organization_name = 'Organization name is required';
    }
    
    if (!formData.subdomain) {
      newErrors.subdomain = 'Subdomain is required';
    }
    
    if (!formData.admin_email) {
      newErrors.admin_email = 'Email is required';
    }
    
    if (!formData.admin_password) {
      newErrors.admin_password = 'Password is required';
    } else if (formData.admin_password.length < 8) {
      newErrors.admin_password = 'Password must be at least 8 characters';
    }
    
    if (formData.admin_password !== formData.admin_confirm_password) {
      newErrors.admin_password = 'Passwords do not match';
    }
    
    if (!formData.admin_first_name) {
      newErrors.admin_first_name = 'First name is required';
    }
    
    if (!formData.admin_last_name) {
      newErrors.admin_last_name = 'Last name is required';
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    setSubmitting(true);
    
    try {
      const response = await apiClient.post('/onboarding/register', {
        organization_name: formData.organization_name,
        subdomain: formData.subdomain,
        admin_email: formData.admin_email,
        admin_password: formData.admin_password,
        admin_first_name: formData.admin_first_name,
        admin_last_name: formData.admin_last_name,
      });
      
      setSuccess(true);
      
      // Redirect to login after 2 seconds
      setTimeout(() => {
        window.location.href = `http://${formData.subdomain}.localhost:3000/login`;
      }, 2000);
      
    } catch (error: any) {
      if (error.response?.data?.errors) {
        const serverErrors: ValidationErrors = {};
        error.response.data.errors.forEach((err: string) => {
          // Parse error messages and map to fields
          if (err.includes('organization')) serverErrors.organization_name = err;
          else if (err.includes('subdomain')) serverErrors.subdomain = err;
          else if (err.includes('email')) serverErrors.admin_email = err;
          else if (err.includes('password')) serverErrors.admin_password = err;
        });
        setErrors(serverErrors);
      } else {
        alert(error.response?.data?.error || 'Registration failed. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (success) {
    return (
      <div className="registration-container">
        <div className="registration-card success-card">
          <div className="success-icon">✅</div>
          <h1>Registration Successful!</h1>
          <p>Your organization <strong>{formData.organization_name}</strong> has been created.</p>
          <p>Redirecting to login page...</p>
          <div className="subdomain-info">
            Your URL: <strong>http://{formData.subdomain}.localhost:3000</strong>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="registration-container">
      <div className="registration-card">
        <div className="registration-header">
          <h1>🏒 Create Your Hockey Team</h1>
          <p>Set up your organization and start managing your pickup games</p>
        </div>

        <form onSubmit={handleSubmit} className="registration-form">
          <div className="form-section">
            <h2>Organization Details</h2>
            
            <div className="form-group">
              <label htmlFor="organization_name">Organization Name *</label>
              <input
                type="text"
                id="organization_name"
                name="organization_name"
                value={formData.organization_name}
                onChange={handleChange}
                onBlur={checkAvailability}
                placeholder="e.g., Downtown Hockey League"
                className={errors.organization_name ? 'error' : ''}
              />
              {errors.organization_name && (
                <span className="error-message">{errors.organization_name}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="subdomain">Subdomain *</label>
              <div className="subdomain-input">
                <input
                  type="text"
                  id="subdomain"
                  name="subdomain"
                  value={formData.subdomain}
                  onChange={handleChange}
                  onBlur={checkAvailability}
                  placeholder="myteam"
                  className={errors.subdomain ? 'error' : ''}
                />
                <span className="subdomain-suffix">.localhost:3000</span>
              </div>
              {errors.subdomain && (
                <span className="error-message">{errors.subdomain}</span>
              )}
              {subdomainSuggestions.length > 0 && (
                <div className="suggestions">
                  <p>Try these available subdomains:</p>
                  <div className="suggestion-chips">
                    {subdomainSuggestions.map(suggestion => (
                      <button
                        key={suggestion}
                        type="button"
                        className="suggestion-chip"
                        onClick={() => setFormData(prev => ({ ...prev, subdomain: suggestion }))}
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              <small className="help-text">This will be your unique URL</small>
            </div>
          </div>

          <div className="form-section">
            <h2>Admin Account</h2>
            
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="admin_first_name">First Name *</label>
                <input
                  type="text"
                  id="admin_first_name"
                  name="admin_first_name"
                  value={formData.admin_first_name}
                  onChange={handleChange}
                  className={errors.admin_first_name ? 'error' : ''}
                />
                {errors.admin_first_name && (
                  <span className="error-message">{errors.admin_first_name}</span>
                )}
              </div>

              <div className="form-group">
                <label htmlFor="admin_last_name">Last Name *</label>
                <input
                  type="text"
                  id="admin_last_name"
                  name="admin_last_name"
                  value={formData.admin_last_name}
                  onChange={handleChange}
                  className={errors.admin_last_name ? 'error' : ''}
                />
                {errors.admin_last_name && (
                  <span className="error-message">{errors.admin_last_name}</span>
                )}
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="admin_email">Email *</label>
              <input
                type="email"
                id="admin_email"
                name="admin_email"
                value={formData.admin_email}
                onChange={handleChange}
                placeholder="admin@example.com"
                className={errors.admin_email ? 'error' : ''}
              />
              {errors.admin_email && (
                <span className="error-message">{errors.admin_email}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="admin_password">Password *</label>
              <input
                type="password"
                id="admin_password"
                name="admin_password"
                value={formData.admin_password}
                onChange={handleChange}
                placeholder="At least 8 characters"
                className={errors.admin_password ? 'error' : ''}
              />
              {errors.admin_password && (
                <span className="error-message">{errors.admin_password}</span>
              )}
              <small className="help-text">
                Must contain uppercase, lowercase, and number
              </small>
            </div>

            <div className="form-group">
              <label htmlFor="admin_confirm_password">Confirm Password *</label>
              <input
                type="password"
                id="admin_confirm_password"
                name="admin_confirm_password"
                value={formData.admin_confirm_password}
                onChange={handleChange}
                placeholder="Re-enter password"
              />
            </div>
          </div>

          <button
            type="submit"
            className="submit-btn"
            disabled={submitting || checking}
          >
            {submitting ? 'Creating Organization...' : 'Create Organization'}
          </button>

          <div className="login-link">
            Already have an account? <a href="/login">Sign in</a>
          </div>
        </form>
      </div>
    </div>
  );
};

export default TenantRegistration;