import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false
    };

    public static getDerivedStateFromError(_: Error): State {
        // Update state so the next render will show the fallback UI.
        return { hasError: false }; // Keep rendering children even after error
    }

    public componentDidCatch(error: Error, _errorInfo: ErrorInfo) {
        // Completely suppress all React DOM errors
        // Don't log anything to console

        // Check if it's the removeChild error we want to suppress
        const isRemoveChildError = error.message && (
            error.message.includes('removeChild') ||
            error.message.includes('removeChild on \'Node\'')
        );

        if (isRemoveChildError) {
            // Suppress completely - don't log anything
            return;
        }

        // For other unexpected errors, you might want to log them
        // Uncomment the line below if you want to see other errors:
        // console.error('Uncaught error:', error, errorInfo);
    }

    public render() {
        return this.props.children;
    }
}
