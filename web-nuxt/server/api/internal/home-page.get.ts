import { getPageByType } from "../../utils/content-api";

export default eventHandler(async () => getPageByType("home"));
