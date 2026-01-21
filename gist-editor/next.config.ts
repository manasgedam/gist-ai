import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Empty turbopack config to acknowledge Next.js 16 default
  turbopack: {},
  
  webpack: (config) => {
    // Fix for Remotion
    config.resolve.alias = {
      ...config.resolve.alias,
      'react-native$': 'react-native-web',
    }
    
    // Allow loading videos from output folder
    config.module.rules.push({
      test: /\.(mp4|webm)$/,
      type: 'asset/resource',
    })
    
    return config
  },
}

export default nextConfig