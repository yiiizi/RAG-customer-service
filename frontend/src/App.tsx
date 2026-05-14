import { App as AntApp } from 'antd';
import { useRoutes } from 'react-router-dom';
import { routes } from './routes';

export default function App() {
  const element = useRoutes(routes);
  return (
    <AntApp>
      {element}
    </AntApp>
  );
}
