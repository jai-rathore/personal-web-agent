/**
 * Application configuration
 */
export const config = {
  api: {
    baseUrl: import.meta.env.VITE_API_BASE || 'http://localhost:8080',
  },
  contact: {
    email: 'jaiadityarathore@gmail.com',
    linkedin: 'https://www.linkedin.com/in/jrathore',
    twitter: 'https://x.com/Jai_A_Rathore',
    github: 'https://github.com/jai-rathore/personal-web-agent',
  },
} as const;

/**
 * Generate email URL
 */
export const getEmailUrl = () => {
  return `mailto:${config.contact.email}`;
};

/**
 * Generate LinkedIn URL
 */
export const getLinkedInUrl = () => {
  return config.contact.linkedin;
};

/**
 * Generate Twitter/X URL
 */
export const getTwitterUrl = () => {
  return config.contact.twitter;
};

/**
 * Generate GitHub URL
 */
export const getGitHubUrl = () => {
  return config.contact.github;
};