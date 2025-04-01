import * as React from 'react';

// Button component types
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
  size?: 'default' | 'sm' | 'lg' | 'icon';
  asChild?: boolean;
}

// Input component types
export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

// Label component types
export interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {}

// Card component types
export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {}

// Declare the components
declare module '../../components/ui/button' {
  export const Button: React.ForwardRefExoticComponent<ButtonProps & React.RefAttributes<HTMLButtonElement>>;
  export const buttonVariants: (props: ButtonProps) => string;
}

declare module '../../components/ui/input' {
  export const Input: React.ForwardRefExoticComponent<InputProps & React.RefAttributes<HTMLInputElement>>;
}

declare module '../../components/ui/label' {
  export const Label: React.ForwardRefExoticComponent<LabelProps & React.RefAttributes<HTMLLabelElement>>;
}

declare module '../../components/ui/card' {
  export const Card: React.ForwardRefExoticComponent<CardProps & React.RefAttributes<HTMLDivElement>>;
  export const CardHeader: React.ForwardRefExoticComponent<CardProps & React.RefAttributes<HTMLDivElement>>;
  export const CardTitle: React.ForwardRefExoticComponent<CardProps & React.RefAttributes<HTMLHeadingElement>>;
  export const CardDescription: React.ForwardRefExoticComponent<CardProps & React.RefAttributes<HTMLParagraphElement>>;
  export const CardContent: React.ForwardRefExoticComponent<CardProps & React.RefAttributes<HTMLDivElement>>;
  export const CardFooter: React.ForwardRefExoticComponent<CardProps & React.RefAttributes<HTMLDivElement>>;
} 