type LogLevel = "DEBUG" | "INFO" | "WARNING" | "ERROR";

const formatTimestamp = (): string => {
  const now = new Date();
  const pad = (n: number, len = 2) => String(n).padStart(len, "0");
  const date = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
  const time = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())},${pad(now.getMilliseconds(), 3)}`;

  return `${date} ${time}`;
};

const formatMessage = (
  level: LogLevel,
  module: string,
  message: string,
): string => {
  return `[${formatTimestamp()}] ${level} [${module}]: ${message}`;
};

export const createLogger = (module: string) => {
  return {
    debug: (message: string) =>
      console.debug(formatMessage("DEBUG", module, message)),
    info: (message: string) =>
      console.info(formatMessage("INFO", module, message)),
    warn: (message: string) =>
      console.warn(formatMessage("WARNING", module, message)),
    error: (message: string) =>
      console.error(formatMessage("ERROR", module, message)),
  };
};
