export const TIAN_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
export const DI_ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

export function getJieqi(year, x) {
  if (x < 1 || x > 24 || year < 1900) return null
  const xAdj = x - 1
  const startDate = new Date(1899, 11, 31) // Dec 31, 1899
  const days = 365.242 * (year - 1900) + 6.2 + 15.22 * xAdj - 1.9 * Math.sin(0.262 * xAdj)
  const result = new Date(startDate.getTime())
  result.setDate(result.getDate() + Math.floor(days))
  return result
}

export function getYearGanZhi(date) {
  const year = date.getFullYear()
  if (year < 1900) return ["", ""]
  const spring = getJieqi(year, 3) // Swift uses x=3
  let y = year
  if (date < spring) y -= 1
  const ganIndex = ((y - 4) % 10 + 10) % 10
  const zhiIndex = ((y - 4) % 12 + 12) % 12
  return [TIAN_GAN[ganIndex], DI_ZHI[zhiIndex]]
}

export function getYearGanZhiNum(date) {
  const [gan, zhi] = getYearGanZhi(date)
  return [TIAN_GAN.indexOf(gan) + 1, DI_ZHI.indexOf(zhi) + 1]
}

export function getMonthGanZhi(date) {
  const year = date.getFullYear()
  if (year < 1900) return ["", ""]

  const jieqiDates = []
  for (let i = 1; i < 24; i += 2) {
    const jd = getJieqi(year, i)
    if (jd) jieqiDates.push(jd)
  }

  let zhiIndex = 0
  const startZhi = 1
  for (let j = 0; j < jieqiDates.length; j++) {
    if (date >= jieqiDates[j]) {
      zhiIndex = startZhi + j
    }
  }

  const ganList = { 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 7, 9: 8, 10: 9, 11: 10, 0: 11, 1: 12 }
  const yearGan = getYearGanZhiNum(date)[0]
  let ganIndex = (yearGan * 2 + ganList[zhiIndex]) % 10
  if (ganIndex === 0) ganIndex = 10
  ganIndex -= 1

  return [TIAN_GAN[ganIndex], DI_ZHI[zhiIndex]]
}

export function getDayGanZhi(date) {
  const startGanZhi = 16 // 1901-01-01 = 乙卯日
  const msPerDay = 86400000
  const d1 = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  const d2 = new Date(1901, 0, 1)
  const days = Math.round((d1 - d2) / msPerDay)
  if (days < 0) return ["", ""]

  let res = (startGanZhi + days) % 60
  if (res === 0) res = 60

  const ganIndex = (res - 1) % 10
  const zhiIndex = (res - 1) % 12
  return [TIAN_GAN[ganIndex], DI_ZHI[zhiIndex]]
}

export function getHourZhi(hour) {
  const cnt = Math.floor((hour + 1) / 2)
  return cnt === 12 ? 0 : cnt
}

export function getHourGanZhi(date) {
  const hour = date.getHours()
  const zhiHour = getHourZhi(hour)

  const startDate = new Date(1901, 0, 1, 1, 0, 0)
  const startGanZhi = 1

  const hours = Math.floor((date - startDate) / 3600000)
  const ganIndex = ((startGanZhi + Math.floor(hours / 2)) % 10 + 10) % 10

  return [TIAN_GAN[ganIndex], DI_ZHI[zhiHour]]
}

export function getBaZi(date) {
  return [
    getYearGanZhi(date),
    getMonthGanZhi(date),
    getDayGanZhi(date),
    getHourGanZhi(date)
  ]
}

export function formatBaZi(date) {
  const bazi = getBaZi(date)
  return bazi.map(([g, z]) => g + z).join(' ')
}
