import React, { useEffect, useState } from 'react';
import './LoginBackground.css';

interface LoginBackgroundProps {
  theme: string;
}

const LoginBackground: React.FC<LoginBackgroundProps> = ({ theme }) => {
  const [animationElements, setAnimationElements] = useState<JSX.Element[]>([]);

  useEffect(() => {
    // 为各种主题创建动画元素
    if (theme === 'tech') {
      createTechElements();
    } else if (theme === 'dark') {
      createDarkElements();
    } else if (theme === 'gradient') {
      createGradientElements();
    } else if (theme === 'minimal') {
      createMinimalElements();
    } else if (theme === 'light') {
      createLightElements();
    }
  }, [theme]);

  // 为科技主题创建动画元素
  const createTechElements = () => {
    const particles: JSX.Element[] = [];
    const rainColumns: JSX.Element[] = [];
    
    // 创建粒子
    for (let i = 0; i < 50; i++) {
      const size = Math.random() * 4 + 2;
      const x = Math.random() * 100;
      const y = Math.random() * 100;
      const duration = Math.random() * 15 + 5;
      const delay = Math.random() * 5;
      
      particles.push(
        <div
          key={`particle-${i}`}
          className="particle"
          style={{
            width: `${size}px`,
            height: `${size}px`,
            left: `${x}%`,
            top: `${y}%`,
            opacity: Math.random() * 0.5 + 0.2,
            animation: `float ${duration}s infinite linear ${delay}s`
          }}
        />
      );
    }
    
    // 创建数字雨
    const characters = '01'.split('');
    for (let i = 0; i < 15; i++) {
      const x = Math.random() * 100;
      const duration = Math.random() * 10 + 10;
      const delay = Math.random() * 10;
      const chars: JSX.Element[] = [];
      
      for (let j = 0; j < 15; j++) {
        const char = characters[Math.floor(Math.random() * characters.length)];
        const opacity = Math.random() * 0.8 + 0.2;
        
        chars.push(
          <div
            key={`char-${i}-${j}`}
            className="rain-char"
            style={{
              top: `${j * 20}px`,
              opacity
            }}
          >
            {char}
          </div>
        );
      }
      
      rainColumns.push(
        <div
          key={`rain-${i}`}
          className="rain-column"
          style={{
            left: `${x}%`,
            animation: `rainFall ${duration}s infinite linear ${delay}s`
          }}
        >
          {chars}
        </div>
      );
    }
    
    setAnimationElements([
      <div key="tech-bg" className="login-bg-animated">
        <div className="login-tech-circuit" />
        <div className="login-tech-glow" />
        <div className="particles">{particles}</div>
        <div className="digital-rain">{rainColumns}</div>
      </div>
    ]);
  };
  
  // 为暗色主题创建动画元素
  const createDarkElements = () => {
    const stars: JSX.Element[] = [];
    const shootingStars: JSX.Element[] = [];
    
    // 创建星星
    for (let i = 0; i < 100; i++) {
      const size = Math.random() * 2 + 1;
      const x = Math.random() * 100;
      const y = Math.random() * 100;
      const duration = Math.random() * 5 + 2;
      const delay = Math.random() * 5;
      
      stars.push(
        <div
          key={`star-${i}`}
          className="star"
          style={{
            width: `${size}px`,
            height: `${size}px`,
            left: `${x}%`,
            top: `${y}%`,
            animation: `twinkle ${duration}s infinite alternate ${delay}s`
          }}
        />
      );
    }
    
    // 创建流星
    for (let i = 0; i < 5; i++) {
      const x = Math.random() * 80;
      const y = Math.random() * 40;
      const duration = Math.random() * 5 + 5;
      const delay = Math.random() * 15;
      
      shootingStars.push(
        <div
          key={`shooting-${i}`}
          className="shooting-star"
          style={{
            left: `${x}%`,
            top: `${y}%`,
            animation: `shooting ${duration}s infinite ${delay}s`
          }}
        />
      );
    }
    
    setAnimationElements([
      <div key="dark-bg" className="login-bg-animated" style={{ backgroundColor: '#121212' }}>
        <div className="login-dots-pattern" />
        <div className="login-dark-glow" />
        <div className="stars">{stars}</div>
        <div className="shooting-stars">{shootingStars}</div>
      </div>
    ]);
  };
  
  // 为渐变主题创建动画元素
  const createGradientElements = () => {
    const bubbles: JSX.Element[] = [];
    
    // 创建浮动气泡
    for (let i = 0; i < 20; i++) {
      const size = Math.random() * 80 + 40;
      const x = Math.random() * 100;
      const y = Math.random() * 100 + 50;
      const duration = Math.random() * 20 + 20;
      const delay = Math.random() * 10;
      
      bubbles.push(
        <div
          key={`bubble-${i}`}
          className="bubble"
          style={{
            width: `${size}px`,
            height: `${size}px`,
            left: `${x}%`,
            top: `${y}%`,
            animation: `bubbleRise ${duration}s infinite linear ${delay}s`
          }}
        />
      );
    }
    
    setAnimationElements([
      <div key="gradient-bg" className="login-bg-animated">
        <div className="login-gradient-waves" />
        <div className="bubbles">{bubbles}</div>
      </div>
    ]);
  };
  
  // 为极简主题创建动画元素
  const createMinimalElements = () => {
    const squares: JSX.Element[] = [];
    const points: JSX.Element[] = [];
    
    // 创建漂浮方块
    for (let i = 0; i < 10; i++) {
      const size = Math.random() * 40 + 20;
      const x = Math.random() * 100;
      const y = Math.random() * 100;
      const duration = Math.random() * 20 + 20;
      const delay = Math.random() * 5;
      
      squares.push(
        <div
          key={`square-${i}`}
          className="floating-square"
          style={{
            width: `${size}px`,
            height: `${size}px`,
            left: `${x}%`,
            top: `${y}%`,
            animation: `squareFloat ${duration}s infinite linear ${delay}s`
          }}
        />
      );
    }
    
    // 创建交叉点
    for (let i = 0; i < 50; i++) {
      const x = i % 10 * 10 + Math.random() * 5;
      const y = Math.floor(i / 10) * 10 + Math.random() * 5;
      const duration = Math.random() * 3 + 2;
      const delay = Math.random() * 3;
      
      points.push(
        <div
          key={`point-${i}`}
          className="intersection-point"
          style={{
            left: `${x}%`,
            top: `${y}%`,
            animation: `pointPulse ${duration}s infinite alternate ${delay}s`
          }}
        />
      );
    }
    
    setAnimationElements([
      <div key="minimal-bg" className="login-bg-animated minimal-bg">
        <div className="minimal-grid" />
        <div className="floating-squares">{squares}</div>
        <div className="intersection-points">{points}</div>
      </div>
    ]);
  };
  
  // 为浅色主题创建动画元素
  const createLightElements = () => {
    const ripples: JSX.Element[] = [];
    const particles: JSX.Element[] = [];
    
    // 创建波纹
    for (let i = 0; i < 5; i++) {
      const x = Math.random() * 100;
      const y = Math.random() * 100;
      const duration = Math.random() * 10 + 8;
      const delay = Math.random() * 8;
      
      ripples.push(
        <div
          key={`ripple-${i}`}
          className="light-ripple"
          style={{
            left: `${x}%`,
            top: `${y}%`,
            animation: `rippleExpand ${duration}s infinite ease-out ${delay}s`
          }}
        />
      );
    }
    
    // 创建光点
    for (let i = 0; i < 30; i++) {
      const size = Math.random() * 5 + 2;
      const x = Math.random() * 100;
      const y = Math.random() * 100;
      const duration = Math.random() * 15 + 15;
      const delay = Math.random() * 5;
      
      particles.push(
        <div
          key={`light-particle-${i}`}
          className="light-particle"
          style={{
            width: `${size}px`,
            height: `${size}px`,
            left: `${x}%`,
            top: `${y}%`,
            animation: `lightFloat ${duration}s infinite linear ${delay}s`
          }}
        />
      );
    }
    
    setAnimationElements([
      <div key="light-bg" className="login-bg-animated light-bg">
        <div className="light-pattern" />
        <div className="light-ripples">{ripples}</div>
        <div className="light-particles">{particles}</div>
      </div>
    ]);
  };

  return (
    <>
      {animationElements}
    </>
  );
};

export default LoginBackground; 